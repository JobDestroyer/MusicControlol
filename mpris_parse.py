"""Parse dbus-send --print-reply text for MPRIS properties."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def parse_variant_string(stdout: str) -> str:
    quotes = re.findall(r'"([^"]*)"', stdout)
    if quotes:
        return quotes[-1]
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return ""
    parts = lines[-1].split()
    return parts[-1] if parts else ""


def parse_variant_number(stdout: str) -> float:
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return 0.0
    parts = lines[-1].split()
    try:
        return float(parts[-1])
    except Exception:
        return 0.0


def parse_variant_bool(stdout: str) -> bool:
    return bool(re.search(r"\btrue\b", stdout, re.I))


def parse_metadata(stdout: str) -> Dict[str, Any]:
    """
    Best-effort parse of dbus-send Metadata (or GetAll blob containing Metadata).
    Handles multi-artist arrays and titles with most punctuation.
    """
    text = stdout
    out: Dict[str, Any] = {}

    def grab(key: str, patterns: List[str]) -> None:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                out[key] = m.group(1).strip()
                return

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
    Parse Properties.GetAll for org.mpris.MediaPlayer2.Player.
    Returns flat keys used by the UI.
    """
    result: Dict[str, Any] = {
        "playbackStatus": "Stopped",
        "position": 0,
        "volume": 0.0,
        "canSeek": False,
        "canControlVolume": False,
        "metadata": {},
    }

    # PlaybackStatus
    m = re.search(
        r'string\s+"PlaybackStatus".*?string\s+"([^"]*)"',
        stdout,
        re.I | re.S,
    )
    if m:
        result["playbackStatus"] = m.group(1)

    # Position
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

    # Volume
    m = re.search(
        r'string\s+"Volume".*?(?:double)\s+(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)',
        stdout,
        re.I | re.S,
    )
    if m:
        try:
            result["volume"] = float(m.group(1))
            result["canControlVolume"] = True
        except Exception:
            pass

    # CanSeek
    m = re.search(
        r'string\s+"CanSeek".*?boolean\s+(true|false)',
        stdout,
        re.I | re.S,
    )
    if m:
        result["canSeek"] = m.group(1).lower() == "true"

    # Metadata: slice from the Metadata key through the rest of the dump
    # (nested arrays make a strict end-anchor unreliable).
    meta_m = re.search(r'string\s+"Metadata"(.*)\Z', stdout, re.I | re.S)
    if meta_m:
        result["metadata"] = parse_metadata(meta_m.group(1))
    else:
        result["metadata"] = parse_metadata(stdout)

    return result


def identity_from_bus_name(bus_name: str) -> str:
    return bus_name.replace("org.mpris.MediaPlayer2.", "")
