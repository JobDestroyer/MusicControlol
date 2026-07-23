"""
mpris_parse.py
==============

Purpose
-------
Turn the *human-readable text* that ``dbus-send --print-reply`` prints
into plain Python dicts / strings / numbers that the UI can use.

Background: why we parse text at all
------------------------------------
The MPRIS D-Bus API is typed (strings, int64, object paths, arrays, etc.).
A native D-Bus library would give us those types directly.

This plugin deliberately uses ``dbus-send`` (a CLI tool shipped with
SteamOS) because it is reliable from inside the Decky sandbox and does
not require vendored C extensions. The tradeoff is that we get stdout
text like::

    method return time=...
       variant       string "Playing"

and must scrape it with regular expressions.

These parsers are intentionally "best effort":

* They handle the shapes produced by Strawberry, Spotify, Firefox, etc.
* They may miss exotic edge cases (weird nested types). When that happens
  the UI simply shows defaults rather than crashing.

What "variant" means in the dumps
---------------------------------
D-Bus properties are returned as *variants* — a type tag plus a value.
dbus-send prints that as several lines, e.g.::

    variant       string "Hello"
    variant       int64 12345
    variant       boolean true
    variant       object path "/org/mpris/MediaPlayer2/Track/1"
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def parse_variant_string(stdout: str) -> str:
    """
    Extract a string value from a single-property Get reply.

    Strategy: collect every double-quoted substring; the *last* one is
    almost always the property value (earlier quotes may be type names
    or path fragments in the method-return header).

    Falls back to the last whitespace-separated token if there are no quotes.
    """
    quotes = re.findall(r'"([^"]*)"', stdout)
    if quotes:
        return quotes[-1]
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return ""
    parts = lines[-1].split()
    return parts[-1] if parts else ""


def parse_variant_number(stdout: str) -> float:
    """
    Extract a numeric value (int64 / uint64 / double) from a Get reply.

    Looks at the last non-empty line and takes its last token.
    Returns 0.0 if nothing parseable is found.
    """
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return 0.0
    parts = lines[-1].split()
    try:
        return float(parts[-1])
    except Exception:
        return 0.0


def parse_variant_bool(stdout: str) -> bool:
    """
    True if the reply text contains the word ``true`` (case-insensitive).

    Used for properties like ``CanSeek``.
    """
    return bool(re.search(r"\btrue\b", stdout, re.I))


def parse_metadata(stdout: str) -> Dict[str, Any]:
    """
    Parse an MPRIS ``Metadata`` property dump into a flat UI-friendly dict.

    Input is either:
      * The stdout of ``Properties.Get ... Metadata``, or
      * A substring of a ``Properties.GetAll`` dump that contains Metadata.

    Output keys (all optional — missing means "unknown"):
      * ``trackid``  — object path or string id (needed for SetPosition/seek)
      * ``artUrl``   — ``file://...`` or ``https://...`` cover art
      * ``title``    — track title
      * ``album``    — album name
      * ``artist``   — comma-joined list if multiple artists (Strawberry)
      * ``length``   — track length in **microseconds** (MPRIS standard)
      * ``url``      — media file/stream URL if present

    Multi-artist handling
    ---------------------
    MPRIS defines ``xesam:artist`` as an *array of strings*. dbus-send
    prints that as::

        string "xesam:artist"
        variant  array [
              string "A"
              string "B"
           ]

    We join with ``", "`` so the frontend can show a single line.
    """
    text = stdout
    out: Dict[str, Any] = {}

    def grab(key: str, patterns: List[str]) -> None:
        """Try each regex until one matches; store capture group 1 under key."""
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                out[key] = m.group(1).strip()
                return

    # trackid: usually an object path for "proper" players (Strawberry);
    # Spotify sometimes uses a plain string like "spotify:track:..."
    grab(
        "trackid",
        [
            r'mpris:trackid".*?object path\s+"([^"]+)"',
            r'mpris:trackid".*?string\s+"([^"]*)"',
        ],
    )
    grab("artUrl", [r'mpris:artUrl".*?string\s+"([^"]*)"'])
    grab("title", [r'xesam:title".*?string\s+"([^"]*)"'])
    grab("album", [r'xesam:album".*?string\s+"([^"]*)"'])
    grab("url", [r'xesam:url".*?string\s+"([^"]*)"'])

    # length is int64/uint64 microseconds
    m = re.search(
        r'mpris:length".*?(?:int64|uint64|double)\s+(-?\d+(?:\.\d+)?)',
        text,
        re.I | re.S,
    )
    if m:
        try:
            out["length"] = int(float(m.group(1)))
        except Exception:
            pass

    # artists as array preferred; single string fallback
    artists_block = re.findall(r'xesam:artist".*?array\s*\[(.*?)\]', text, re.I | re.S)
    if artists_block:
        names = re.findall(r'string\s+"([^"]*)"', artists_block[0])
        if names:
            out["artist"] = ", ".join(names)
    else:
        grab("artist", [r'xesam:artist".*?string\s+"([^"]*)"'])

    return out


def parse_player_get_all(stdout: str) -> Dict[str, Any]:
    """
    Parse ``Properties.GetAll`` for interface ``org.mpris.MediaPlayer2.Player``.

    One GetAll is cheaper than five separate Get calls (PlaybackStatus,
    Position, Volume, CanSeek, Metadata) — important because the UI polls
    about once per second while the panel is open.

    Returns a dict with fixed keys the frontend expects::

        {
          "playbackStatus": "Playing" | "Paused" | "Stopped",
          "position": int,          # microseconds into the track
          "volume": float,          # 0.0 .. 1.0
          "canSeek": bool,
          "canControlVolume": bool, # True if Volume property was present
          "metadata": { ... },      # see parse_metadata()
        }
    """
    result: Dict[str, Any] = {
        "playbackStatus": "Stopped",
        "position": 0,
        "volume": 0.0,
        "canSeek": False,
        "canControlVolume": False,
        "metadata": {},
    }

    # --- PlaybackStatus (string) ------------------------------------------
    m = re.search(
        r'string\s+"PlaybackStatus".*?string\s+"([^"]*)"',
        stdout,
        re.I | re.S,
    )
    if m:
        result["playbackStatus"] = m.group(1)

    # --- Position (int64 microseconds) ------------------------------------
    m = re.search(
        r'string\s+"Position".*?(?:int64|uint64)\s+(-?\d+)',
        stdout,
        re.I | re.S,
    )
    if m:
        try:
            result["position"] = int(m.group(1))
        except Exception:
            pass

    # --- Volume (double 0..1) ---------------------------------------------
    m = re.search(
        r'string\s+"Volume".*?(?:double)\s+(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',
        stdout,
        re.I | re.S,
    )
    if m:
        try:
            result["volume"] = float(m.group(1))
            # If the property exists and is readable, the UI may show a slider
            result["canControlVolume"] = True
        except Exception:
            pass

    # --- CanSeek (boolean) ------------------------------------------------
    m = re.search(
        r'string\s+"CanSeek".*?boolean\s+(true|false)',
        stdout,
        re.I | re.S,
    )
    if m:
        result["canSeek"] = m.group(1).lower() == "true"

    # --- Metadata (nested a{sv}) ------------------------------------------
    # Nested arrays make a precise end-anchor hard; take everything after
    # the "Metadata" key and let parse_metadata pick out the fields it knows.
    meta_m = re.search(r'string\s+"Metadata"(.*)\Z', stdout, re.I | re.S)
    if meta_m:
        result["metadata"] = parse_metadata(meta_m.group(1))
    else:
        result["metadata"] = parse_metadata(stdout)

    return result


def identity_from_bus_name(bus_name: str) -> str:
    """
    Human-ish fallback label when we cannot read the MPRIS Identity property.

    ``org.mpris.MediaPlayer2.strawberry`` → ``strawberry``
    """
    return bus_name.replace("org.mpris.MediaPlayer2.", "")
