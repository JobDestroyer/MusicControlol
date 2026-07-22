"""Session bus discovery for SteamOS / Decky Game Mode."""

from __future__ import annotations

import os
import pwd
import re
import subprocess
from typing import List, Tuple

MPRIS_PREFIX = "org.mpris.MediaPlayer2"


def deck_uid() -> int:
    for name in (
        os.environ.get("DECKY_USER"),
        os.environ.get("USER"),
        "deck",
    ):
        if not name:
            continue
        try:
            return pwd.getpwnam(name).pw_uid
        except Exception:
            pass
    return os.getuid()


def bus_candidates() -> List[str]:
    out: List[str] = []
    seen = set()

    def add(addr: str) -> None:
        addr = (addr or "").strip().strip('"')
        if not addr or addr in seen:
            return
        if addr.startswith("unix:path="):
            path = addr[len("unix:path=") :].split(",")[0]
            if not os.path.exists(path):
                return
            addr = f"unix:path={path}"
        elif addr.startswith("/"):
            if not os.path.exists(addr):
                return
            addr = f"unix:path={addr}"
        seen.add(addr)
        out.append(addr)

    uid = deck_uid()
    add(f"unix:path=/run/user/{uid}/bus")
    add(f"unix:path=/run/user/{os.getuid()}/bus")
    add(os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""))
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    add(f"unix:path={os.path.join(xdg, 'bus')}")

    try:
        for name in os.listdir("/run/user"):
            if name.isdigit():
                add(f"unix:path=/run/user/{name}/bus")
    except Exception:
        pass

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
                    raw = f.read()
                for item in raw.split(b"\0"):
                    if item.startswith(b"DBUS_SESSION_BUS_ADDRESS="):
                        add(item.split(b"=", 1)[1].decode("utf-8", "replace"))
            except Exception:
                continue
    except Exception:
        pass

    return out


def run_dbus_send(bus_addr: str, args: List[str], timeout: float = 2.0) -> str:
    env = os.environ.copy()
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
        raise RuntimeError("dbus-send not found") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("dbus-send timed out") from e
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or f"dbus-send exit {proc.returncode}")
    return proc.stdout or ""


def parse_list_names(stdout: str) -> List[str]:
    names: List[str] = []
    for line in stdout.splitlines():
        if MPRIS_PREFIX not in line:
            continue
        m = re.search(r'"([^"]+)"', line)
        if m and m.group(1).startswith(MPRIS_PREFIX):
            names.append(m.group(1))
    return sorted(set(names))


def list_mpris_names(bus_addr: str) -> List[str]:
    out = run_dbus_send(
        bus_addr,
        [
            "--dest=org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus.ListNames",
        ],
        timeout=2.0,
    )
    return parse_list_names(out)


def discover_players() -> Tuple[List[str], str]:
    """Return (mpris_bus_names, session_bus_address)."""
    first_ok = ""
    for addr in bus_candidates():
        try:
            names = list_mpris_names(addr)
            if names:
                return names, addr
            first_ok = first_ok or addr
        except Exception:
            continue
    return [], first_ok
