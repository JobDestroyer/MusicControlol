"""
MusicControl backend — control MPRIS players on the user session bus via dbus-send.
"""

from __future__ import annotations

import asyncio
import os
import pwd
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote, urlparse

_plugin_dir = os.path.dirname(os.path.abspath(__file__))
# Decky loads main.py by path; the plugin folder is not on sys.path by default.
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

import decky  # type: ignore

MPRIS_PREFIX = "org.mpris.MediaPlayer2"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
IFACE_ROOT = "org.mpris.MediaPlayer2"
IFACE_PLAYER = "org.mpris.MediaPlayer2.Player"


def _deck_uid() -> int:
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


def _bus_candidates() -> List[str]:
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

    uid = _deck_uid()
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


def _run_dbus_send(bus_addr: str, args: List[str], timeout: float = 2.0) -> str:
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


def _parse_list_names(stdout: str) -> List[str]:
    names: List[str] = []
    for line in stdout.splitlines():
        if "org.mpris.MediaPlayer2" not in line:
            continue
        m = re.search(r'"([^"]+)"', line)
        if m and m.group(1).startswith(MPRIS_PREFIX):
            names.append(m.group(1))
    return sorted(set(names))


def _list_mpris_on_bus(bus_addr: str) -> List[str]:
    out = _run_dbus_send(
        bus_addr,
        [
            "--dest=org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus.ListNames",
        ],
        timeout=2.0,
    )
    return _parse_list_names(out)


def discover_players() -> Tuple[List[str], str]:
    candidates = _bus_candidates()
    first_ok = ""
    for addr in candidates:
        try:
            names = _list_mpris_on_bus(addr)
            if names:
                return names, addr
            first_ok = first_ok or addr
        except Exception:
            continue
    return [], first_ok


def _prop_get(bus_addr: str, dest: str, iface: str, prop: str) -> str:
    return _run_dbus_send(
        bus_addr,
        [
            f"--dest={dest}",
            MPRIS_PATH,
            "org.freedesktop.DBus.Properties.Get",
            f"string:{iface}",
            f"string:{prop}",
        ],
        timeout=2.0,
    )


def _parse_variant_string(stdout: str) -> str:
    quotes = re.findall(r'"([^"]*)"', stdout)
    if quotes:
        return quotes[-1]
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return ""
    parts = lines[-1].split()
    return parts[-1] if parts else ""


def _parse_variant_number(stdout: str) -> float:
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    if not lines:
        return 0.0
    parts = lines[-1].split()
    try:
        return float(parts[-1])
    except Exception:
        return 0.0


def _parse_metadata(stdout: str) -> Dict[str, Any]:
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
            r'mpris:trackid".*?string\s+"([^"]+)"',
        ],
    )
    grab("artUrl", [r'mpris:artUrl".*?string\s+"([^"]+)"'])
    grab("title", [r'xesam:title".*?string\s+"([^"]+)"'])
    grab("album", [r'xesam:album".*?string\s+"([^"]+)"'])

    m = re.search(
        r'mpris:length".*?(?:int64|uint64|double)\s+(-?\d+)', text, re.I | re.S
    )
    if m:
        try:
            out["length"] = int(m.group(1))
        except Exception:
            pass

    artists = re.findall(r'xesam:artist".*?array\s*\[(.*?)\]', text, re.I | re.S)
    if artists:
        names = re.findall(r'string\s+"([^"]+)"', artists[0])
        if names:
            out["artist"] = ", ".join(names)
    else:
        grab("artist", [r'xesam:artist".*?string\s+"([^"]+)"'])

    return out


def _player_call(bus_addr: str, dest: str, method: str) -> None:
    _run_dbus_send(
        bus_addr,
        [f"--dest={dest}", MPRIS_PATH, f"{IFACE_PLAYER}.{method}"],
        timeout=2.0,
    )


class Plugin:
    def __init__(self) -> None:
        self.player = ""
        self.bus_address = ""
        self.previous_cached_image = ""
        self.cache_dir = ""
        self.symlink_path = ""

    async def _run(self, fn, *args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)

    async def _main(self) -> None:
        self.cache_dir = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "cache")
        self.symlink_path = os.path.join(
            decky.DECKY_USER_HOME,
            ".local/share/Steam/steamui/images/deckycache_musicControl",
        )
        self.player = ""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
        except Exception:
            pass
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            if not os.path.exists(self.symlink_path):
                os.makedirs(os.path.dirname(self.symlink_path), exist_ok=True)
                os.symlink(self.cache_dir, self.symlink_path, target_is_directory=True)
        except Exception:
            pass

        names, addr = await self._run(discover_players)
        self.bus_address = addr
        if addr:
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
        decky.logger.info(
            f"MusicControl ready bus={addr!r} players={len(names)}"
        )

    async def _unload(self) -> None:
        pass

    async def list_players(self) -> List[Dict[str, str]]:
        try:
            names, addr = await self._run(discover_players)
            self.bus_address = addr or self.bus_address
            if addr:
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr

            players: List[Dict[str, str]] = []
            for name in names:
                identity = name.replace(MPRIS_PREFIX + ".", "")
                if addr:
                    try:
                        raw = await self._run(
                            _prop_get, addr, name, IFACE_ROOT, "Identity"
                        )
                        identity = _parse_variant_string(raw) or identity
                    except Exception:
                        pass
                players.append({"busName": name, "identity": identity})
            return players
        except Exception as e:
            decky.logger.error(f"list_players: {e}")
            return []

    async def set_player(self, player: str) -> str:
        self.player = player or ""
        return self.player

    async def get_player(self) -> str:
        return self.player

    async def get_status(self) -> Dict[str, Any]:
        empty: Dict[str, Any] = {
            "available": False,
            "hasTrack": False,
            "player": self.player,
            "identity": "",
            "playbackStatus": "Stopped",
            "position": 0,
            "volume": 0.0,
            "canSeek": False,
            "canControlVolume": False,
            "metadata": {},
            "error": "",
        }
        try:
            if not self.bus_address or not self.player:
                names, addr = await self._run(discover_players)
                if addr:
                    self.bus_address = addr
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
                if not self.player and names:
                    self.player = names[0]
                if not names:
                    return empty

            bus = self.bus_address
            dest = self.player
            if not bus or not dest:
                return empty

            meta_raw = await self._run(_prop_get, bus, dest, IFACE_PLAYER, "Metadata")
            metadata = _parse_metadata(meta_raw)

            try:
                st_raw = await self._run(
                    _prop_get, bus, dest, IFACE_PLAYER, "PlaybackStatus"
                )
                status = _parse_variant_string(st_raw) or "Stopped"
            except Exception:
                status = "Stopped"

            try:
                pos_raw = await self._run(_prop_get, bus, dest, IFACE_PLAYER, "Position")
                position = int(_parse_variant_number(pos_raw))
            except Exception:
                position = 0

            volume = 0.0
            can_volume = False
            try:
                vol_raw = await self._run(_prop_get, bus, dest, IFACE_PLAYER, "Volume")
                volume = float(_parse_variant_number(vol_raw))
                can_volume = True
            except Exception:
                pass

            can_seek = False
            try:
                sk_raw = await self._run(_prop_get, bus, dest, IFACE_PLAYER, "CanSeek")
                if re.search(r"\btrue\b", sk_raw, re.I):
                    can_seek = True
            except Exception:
                pass

            try:
                id_raw = await self._run(_prop_get, bus, dest, IFACE_ROOT, "Identity")
                identity = _parse_variant_string(id_raw) or dest
            except Exception:
                identity = dest

            has_track = bool(
                metadata.get("title")
                or metadata.get("trackid")
                or metadata.get("artUrl")
            )
            return {
                "available": True,
                "hasTrack": has_track,
                "player": dest,
                "identity": identity,
                "playbackStatus": status,
                "position": position,
                "volume": volume,
                "canSeek": can_seek,
                "canControlVolume": can_volume,
                "metadata": metadata,
                "error": "",
            }
        except Exception as e:
            decky.logger.error(f"get_status: {e}")
            empty["error"] = str(e)
            return empty

    async def play_pause(self) -> bool:
        return await self._call("PlayPause")

    async def next_track(self) -> bool:
        return await self._call("Next")

    async def previous_track(self) -> bool:
        return await self._call("Previous")

    async def set_position(self, position: int, track_id: str) -> bool:
        if not self.player or not self.bus_address or not track_id:
            return False
        try:
            await self._run(
                _run_dbus_send,
                self.bus_address,
                [
                    f"--dest={self.player}",
                    MPRIS_PATH,
                    f"{IFACE_PLAYER}.SetPosition",
                    f"objpath:{track_id}",
                    f"int64:{int(position)}",
                ],
            )
            return True
        except Exception:
            return False

    async def set_volume(self, volume: float) -> bool:
        if not self.player or not self.bus_address:
            return False
        try:
            volume = max(0.0, min(1.0, float(volume)))
            await self._run(
                _run_dbus_send,
                self.bus_address,
                [
                    f"--dest={self.player}",
                    MPRIS_PATH,
                    "org.freedesktop.DBus.Properties.Set",
                    f"string:{IFACE_PLAYER}",
                    "string:Volume",
                    f"variant:double:{volume}",
                ],
            )
            return True
        except Exception:
            return False

    async def cache_album_art(self, art_url: str) -> str:
        if not art_url or not art_url.startswith("file:"):
            return art_url or ""
        try:
            path = unquote(urlparse(art_url).path)
            if not path or not os.path.exists(path):
                return ""
            if self.previous_cached_image and os.path.exists(self.previous_cached_image):
                try:
                    os.remove(self.previous_cached_image)
                except Exception:
                    pass
            base = os.path.basename(path) or "cover.jpg"
            stem, ext = os.path.splitext(base)
            safe = f"{stem}_{abs(hash(path)) & 0xFFFFFFFF:x}{ext or '.jpg'}"
            target = os.path.join(self.cache_dir, safe)
            await self._run(shutil.copy2, path, target)
            self.previous_cached_image = target
            return f"https://steamloopback.host/images/deckycache_musicControl/{safe}"
        except Exception:
            return ""

    async def _call(self, method: str) -> bool:
        if not self.player:
            return False
        if not self.bus_address:
            _, addr = await self._run(discover_players)
            self.bus_address = addr
        if not self.bus_address:
            return False
        try:
            await self._run(_player_call, self.bus_address, self.player, method)
            return True
        except Exception:
            return False
