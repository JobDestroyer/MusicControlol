"""
bus_discover.py
===============

Purpose
-------
Figure out *which* D-Bus session bus to talk to, and run low-level
`dbus-send` commands against it.

Why this exists
---------------
On a normal Linux desktop, every GUI app and every terminal share one
session bus (usually at ``unix:path=/run/user/<uid>/bus``).

On Steam Deck / SteamOS **Game Mode** things are messier:

* Decky plugins run in a sandboxed Python process. That process often has
  **no** ``DBUS_SESSION_BUS_ADDRESS`` environment variable, or a wrong one.
* Media apps (Strawberry, Spotify Flatpak, etc.) started from Game Mode
  register on the *user's* real session bus — the same bus Steam itself
  uses.
* If we connect to the wrong socket, ``ListNames`` succeeds but returns
  zero MPRIS players, and the UI shows "No Media Player Found".

So this module:

1. Builds a list of *candidate* bus socket addresses (paths that might work).
2. Tries each until it finds one that answers ``ListNames``.
3. Preferentially returns a bus that already has ``org.mpris.MediaPlayer2.*``
   names registered (i.e. a real media player is up).

Public API used by the rest of the plugin
-----------------------------------------
* ``discover_players()`` → ``(list_of_mpris_names, bus_address)``
* ``run_dbus_send(bus_addr, args)`` → stdout text from dbus-send
* ``list_mpris_names(bus_addr)`` → MPRIS names on that bus only
* ``MPRIS_PREFIX`` constant for filtering
"""

from __future__ import annotations

import os
import pwd
import re
import subprocess
from typing import List, Tuple

# ---------------------------------------------------------------------------
# MPRIS well-known name prefix
#
# Every MPRIS 2 player on the session bus owns a name starting with this.
# Examples:
#   org.mpris.MediaPlayer2.strawberry
#   org.mpris.MediaPlayer2.spotify
#   org.mpris.MediaPlayer2.firefox.instance_1_234
# ---------------------------------------------------------------------------
MPRIS_PREFIX = "org.mpris.MediaPlayer2"


def deck_uid() -> int:
    """
    Return the numeric UID that likely owns the Game Mode session bus.

    Order of preference:
      1. ``DECKY_USER`` — set by Decky Loader to the human user (usually ``deck``)
      2. ``USER`` — process environment
      3. Hardcoded fallback name ``deck`` (Steam Deck default account)
      4. Whatever UID this process is currently running as

    We need a *real* login UID because the session bus socket lives at
    ``/run/user/<uid>/bus``. If Decky briefly runs as a different effective
    UID, ``os.getuid()`` alone can point at the wrong socket.
    """
    for name in (
        os.environ.get("DECKY_USER"),
        os.environ.get("USER"),
        "deck",
    ):
        if not name:
            continue
        try:
            # pwd.getpwnam looks up the account in /etc/passwd (or equivalent)
            return pwd.getpwnam(name).pw_uid
        except Exception:
            # Name doesn't exist on this system — try the next candidate
            pass
    return os.getuid()


def bus_candidates() -> List[str]:
    """
    Build an ordered, de-duplicated list of D-Bus session bus addresses to try.

    Each entry is a string like::

        unix:path=/run/user/1000/bus

    which is the form ``dbus-send`` and most D-Bus libraries understand via
    the ``DBUS_SESSION_BUS_ADDRESS`` environment variable.

    Order matters: we put the most likely addresses first so discovery is
    fast on the common Steam Deck path.
    """
    out: List[str] = []
    seen = set()

    def add(addr: str) -> None:
        """
        Normalize and append one address if it looks usable.

        Normalization rules:
          * Strip whitespace and surrounding quotes.
          * ``unix:path=/foo/bus,guid=...`` → keep only the path part and
            verify the socket file exists.
          * Bare ``/foo/bus`` path → rewrite as ``unix:path=/foo/bus``.
          * Skip empties and duplicates.
        """
        addr = (addr or "").strip().strip('"')
        if not addr or addr in seen:
            return
        if addr.startswith("unix:path="):
            # May include ",guid=xxxx" after the path — strip that for exists()
            path = addr[len("unix:path=") :].split(",")[0]
            if not os.path.exists(path):
                return
            addr = f"unix:path={path}"
        elif addr.startswith("/"):
            # Caller passed a raw filesystem path to the socket
            if not os.path.exists(addr):
                return
            addr = f"unix:path={addr}"
        seen.add(addr)
        out.append(addr)

    uid = deck_uid()

    # --- Most common Steam Deck locations ---------------------------------
    # Primary: deck user's runtime bus
    add(f"unix:path=/run/user/{uid}/bus")
    # Secondary: whatever UID this process actually is
    add(f"unix:path=/run/user/{os.getuid()}/bus")
    # Whatever the environment already claims (may be wrong inside Decky,
    # but sometimes it's correct — still try it)
    add(os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""))
    # XDG_RUNTIME_DIR/bus is the portable form of the same idea
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    add(f"unix:path={os.path.join(xdg, 'bus')}")

    # --- Any other /run/user/*/bus we can see (multi-user edge case) ------
    try:
        for name in os.listdir("/run/user"):
            if name.isdigit():
                add(f"unix:path=/run/user/{name}/bus")
    except Exception:
        # No permission or /run/user missing — ignore
        pass

    # --- Steal the address from the live Steam process --------------------
    # Steam is almost always on the "correct" Game Mode session bus.
    # Reading /proc/<pid>/environ is how many Deck tools find the real
    # DBUS_SESSION_BUS_ADDRESS when their own environment is incomplete.
    try:
        r = subprocess.run(
            ["pgrep", "-u", str(uid), "-x", "steam"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        for pid_s in (r.stdout or "").split():
            try:
                with open(f"/proc/{pid_s}/environ", "rb") as f:
                    # Environ is NUL-separated KEY=VALUE pairs
                    raw = f.read()
                for item in raw.split(b"\0"):
                    if item.startswith(b"DBUS_SESSION_BUS_ADDRESS="):
                        add(item.split(b"=", 1)[1].decode("utf-8", "replace"))
            except Exception:
                # Process may have exited mid-read, or we lack permission
                continue
    except Exception:
        # pgrep missing or timed out — not fatal
        pass

    return out


def run_dbus_send(bus_addr: str, args: List[str], timeout: float = 2.0) -> str:
    """
    Run ``dbus-send --session --print-reply ...`` against a specific bus.

    Parameters
    ----------
    bus_addr:
        Value for ``DBUS_SESSION_BUS_ADDRESS`` (e.g. ``unix:path=/run/user/1000/bus``).
    args:
        Arguments *after* ``dbus-send --session --print-reply``.
        Typical example for a property get::

            [
              "--dest=org.mpris.MediaPlayer2.strawberry",
              "/org/mpris/MediaPlayer2",
              "org.freedesktop.DBus.Properties.Get",
              "string:org.mpris.MediaPlayer2.Player",
              "string:PlaybackStatus",
            ]

    timeout:
        Seconds before we kill the subprocess (avoids hanging the plugin forever).

    Returns
    -------
    The full stdout text of dbus-send (human-readable, not binary).

    Raises
    ------
    RuntimeError
        If dbus-send is missing, times out, or exits non-zero.
    """
    env = os.environ.copy()
    # Force this invocation onto the chosen bus, regardless of parent env
    env["DBUS_SESSION_BUS_ADDRESS"] = bus_addr
    try:
        proc = subprocess.run(
            ["dbus-send", "--session", "--print-reply", *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        # SteamOS normally ships dbus-send; if it's gone, nothing works
        raise RuntimeError("dbus-send not found") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("dbus-send timed out") from e
    if proc.returncode != 0:
        # Prefer stderr; some builds print errors on stdout instead
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or f"dbus-send exit {proc.returncode}")
    return proc.stdout or ""


def parse_list_names(stdout: str) -> List[str]:
    """
    Extract MPRIS well-known names from a ``ListNames`` dbus-send dump.

    dbus-send prints something like::

        method return ...
           array [
              string "org.freedesktop.DBus"
              string "org.mpris.MediaPlayer2.strawberry"
              string ":1.42"
           ]

    We keep only quoted strings that start with ``org.mpris.MediaPlayer2``.
    Unique-name forms like ``:1.42`` are ignored (not useful for control).
    """
    names: List[str] = []
    for line in stdout.splitlines():
        if MPRIS_PREFIX not in line:
            continue
        m = re.search(r'"([^"]+)"', line)
        if m and m.group(1).startswith(MPRIS_PREFIX):
            names.append(m.group(1))
    return sorted(set(names))


def list_mpris_names(bus_addr: str) -> List[str]:
    """
    Ask the bus daemon for all well-known names, return MPRIS ones only.

    This is the cheap "is anything playing that we can control?" check.
    """
    out = run_dbus_send(
        bus_addr,
        [
            "--dest=org.freedesktop.DBus",  # the bus daemon itself
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus.ListNames",
        ],
        timeout=2.0,
    )
    return parse_list_names(out)


def discover_players() -> Tuple[List[str], str]:
    """
    Try every candidate bus; return the first that has MPRIS players.

    Returns
    -------
    (names, bus_address)
        * names: list of ``org.mpris.MediaPlayer2.*`` bus names (may be empty)
        * bus_address: address that answered (may be empty if everything failed)

    Preference:
      1. A bus that has at least one MPRIS name (best).
      2. Else a bus that accepted ListNames but had zero MPRIS (still usable
         later when the user starts a player).
      3. Else ``([], "")``.
    """
    first_ok = ""
    for addr in bus_candidates():
        try:
            names = list_mpris_names(addr)
            if names:
                # Gold: real media players visible on this bus
                return names, addr
            # Bus is alive but nobody is advertising MPRIS yet
            first_ok = first_ok or addr
        except Exception:
            # Socket missing, permission denied, timeout — try next candidate
            continue
    return [], first_ok
