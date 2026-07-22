"""
MusicControl backend — MPRIS over the user session bus.

Primary path: dbus-send (works on SteamOS / Decky).
Optional: jeepney for cleaner property reads.
All blocking I/O runs in a thread so the plugin event loop never hangs.
"""

from __future__ import annotations

import asyncio
import os
import pwd
import re
import shutil
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

_plugin_dir = os.path.dirname(os.path.abspath(__file__))
# Decky loads main.py by path; the plugin folder is NOT on sys.path by default.
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)
_py_modules = os.path.join(_plugin_dir, "py_modules")
if _py_modules not in sys.path:
    sys.path.insert(0, _py_modules)

import decky  # type: ignore

try:
    from mpris_util import metadata_to_dict
except Exception:
    # Last resort: keep backend alive even if helper module is missing
    def metadata_to_dict(raw):  # type: ignore
        return raw if isinstance(raw, dict) else {}

MPRIS_PREFIX = "org.mpris.MediaPlayer2"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
IFACE_ROOT = "org.mpris.MediaPlayer2"
IFACE_PLAYER = "org.mpris.MediaPlayer2.Player"

_HAS_JEEPNEY = False
try:
    from jeepney import DBusAddress, Properties, new_method_call  # type: ignore
    from jeepney.bus_messages import message_bus  # type: ignore
    from jeepney.io.blocking import open_dbus_connection  # type: ignore
    from jeepney.wrappers import DBusErrorResponse  # type: ignore
    from mpris_util import unwrap_variant

    _HAS_JEEPNEY = True
except Exception as _jeepney_err:  # pragma: no cover
    DBusErrorResponse = Exception  # type: ignore
    _jeepney_import_error = _jeepney_err


def _log(msg: str) -> None:
    try:
        decky.logger.info(f"[MusicControl] {msg}")
    except Exception:
        print(f"[MusicControl] {msg}", flush=True)


def _log_err(msg: str) -> None:
    try:
        decky.logger.error(f"[MusicControl] {msg}")
    except Exception:
        print(f"[MusicControl] ERROR {msg}", flush=True)


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
    """Fast, ordered list of session bus socket addresses."""
    out: List[str] = []
    seen = set()

    def add(addr: str) -> None:
        addr = (addr or "").strip().strip('"')
        if not addr or addr in seen:
            return
        # unix:path=/run/user/1000/bus[,guid=...]
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

    # 1) Conventional Deck user bus (what the original plugin used)
    uid = _deck_uid()
    add(f"unix:path=/run/user/{uid}/bus")
    add(f"unix:path=/run/user/{os.getuid()}/bus")

    # 2) Env if present and valid
    add(os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""))

    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    add(f"unix:path={os.path.join(xdg, 'bus')}")

    # 3) Any other /run/user/*/bus we can see (rare)
    try:
        for name in os.listdir("/run/user"):
            if name.isdigit():
                add(f"unix:path=/run/user/{name}/bus")
    except Exception:
        pass

    # 4) Quick peek at steam environ only (not full /proc scan)
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
    # Avoid inheriting a broken address-only partial env
    env.pop("DISPLAY", None)
    try:
        proc = subprocess.run(
            ["dbus-send", "--session", "--print-reply", *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError("dbus-send not found on PATH") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"dbus-send timed out: {' '.join(args[:4])}") from e
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


def discover_players() -> Tuple[List[str], str, str]:
    """Return (players, bus_addr, note). Always returns quickly."""
    candidates = _bus_candidates()
    if not candidates:
        return [], "", "no bus socket candidates"

    notes: List[str] = []
    first_ok = ""
    for addr in candidates:
        try:
            names = _list_mpris_on_bus(addr)
            if names:
                return names, addr, f"ok via dbus-send; jeepney={_HAS_JEEPNEY}"
            first_ok = first_ok or addr
            notes.append(f"{addr}: 0 mpris")
        except Exception as e:
            notes.append(f"{addr}: {e}")

    if first_ok:
        return [], first_ok, "bus reachable, no MPRIS; " + " | ".join(notes[:4])
    return [], "", "no working bus; " + " | ".join(notes[:4])


def _prop_get_dbus_send(bus_addr: str, dest: str, iface: str, prop: str) -> str:
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
    # last quoted string often the value
    quotes = re.findall(r'"([^"]*)"', stdout)
    if quotes:
        return quotes[-1]
    # bare word on last line
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


def _parse_metadata_dbus_send(stdout: str) -> Dict[str, Any]:
    """
    Best-effort parse of dbus-send Metadata dump into flat dict.
    Good enough for title/artist/artUrl/length/trackid.
    """
    # Collect dict-entry blocks loosely
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
    grab(
        "artUrl",
        [r'mpris:artUrl".*?string\s+"([^"]+)"'],
    )
    grab(
        "title",
        [r'xesam:title".*?string\s+"([^"]+)"'],
    )
    grab(
        "album",
        [r'xesam:album".*?string\s+"([^"]+)"'],
    )
    # length int64/uint64
    m = re.search(r'mpris:length".*?(?:int64|uint64|double)\s+(-?\d+)', text, re.I | re.S)
    if m:
        try:
            out["length"] = int(m.group(1))
        except Exception:
            pass
    # artists: first string after xesam:artist
    artists = re.findall(
        r'xesam:artist".*?array\s*\[(.*?)\]',
        text,
        re.I | re.S,
    )
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
        self.last_note = ""
        self.last_error = ""
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
        except Exception as e:
            _log(f"cache clear: {e}")
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            if not os.path.exists(self.symlink_path):
                os.makedirs(os.path.dirname(self.symlink_path), exist_ok=True)
                os.symlink(self.cache_dir, self.symlink_path, target_is_directory=True)
        except Exception as e:
            _log(f"symlink: {e}")

        names, addr, note = await self._run(discover_players)
        self.bus_address = addr
        self.last_note = note
        if addr:
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
        _log(
            f"ready uid={os.getuid()} deck_uid={_deck_uid()} "
            f"jeepney={_HAS_JEEPNEY} bus={addr!r} players={names} note={note}"
        )

    async def _unload(self) -> None:
        _log("unload")

    # ---- always-respond methods (for "waiting for backend" diagnosis) ----

    async def ping(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "version": "2.0.3",
            "uid": os.getuid(),
            "deckUid": _deck_uid(),
            "bus": self.bus_address or os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
            "jeepney": _HAS_JEEPNEY,
            "dbusSend": bool(shutil.which("dbus-send")),
            "note": self.last_note,
            "player": self.player,
        }

    async def debug_info(self) -> Dict[str, Any]:
        try:
            names, addr, note = await self._run(discover_players)
            self.bus_address = addr or self.bus_address
            self.last_note = note
            if addr:
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
        except Exception as e:
            names, addr, note = [], self.bus_address, str(e)
        return {
            "uid": os.getuid(),
            "deckyUser": os.environ.get("DECKY_USER", ""),
            "busAddress": addr or self.bus_address,
            "candidates": await self._run(_bus_candidates),
            "players": names,
            "note": note,
            "error": self.last_error,
            "dbusSend": shutil.which("dbus-send") or "",
            "version": "2.0.3",
            "jeepney": _HAS_JEEPNEY,
        }

    async def list_players(self) -> List[Dict[str, str]]:
        try:
            names, addr, note = await self._run(discover_players)
            self.bus_address = addr or self.bus_address
            self.last_note = note
            self.last_error = "" if names else note
            if addr:
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr

            players: List[Dict[str, str]] = []
            for name in names:
                identity = name.replace(MPRIS_PREFIX + ".", "")
                if addr:
                    try:
                        raw = await self._run(
                            _prop_get_dbus_send, addr, name, IFACE_ROOT, "Identity"
                        )
                        identity = _parse_variant_string(raw) or identity
                    except Exception:
                        pass
                players.append({"busName": name, "identity": identity})
            return players
        except Exception as e:
            self.last_error = str(e)
            _log_err(f"list_players: {e}\n{traceback.format_exc()}")
            return []

    async def set_player(self, player: str) -> str:
        self.player = player or ""
        return self.player

    async def get_player(self) -> str:
        return self.player

    async def get_status(self) -> Dict[str, Any]:
        empty = {
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
            "error": self.last_error or self.last_note or "",
            "busAddress": self.bus_address,
            "discoveryNote": self.last_note,
            "version": "2.0.3",
        }
        try:
            if not self.bus_address:
                names, addr, note = await self._run(discover_players)
                self.bus_address = addr
                self.last_note = note
                if addr:
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
                if not self.player and names:
                    self.player = names[0]
                if not names:
                    empty["error"] = note or "No MPRIS players"
                    return empty

            if not self.player:
                names, addr, note = await self._run(discover_players)
                self.last_note = note
                if addr:
                    self.bus_address = addr
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
                if not names:
                    empty["error"] = note or "No MPRIS players"
                    return empty
                self.player = names[0]

            bus = self.bus_address
            dest = self.player

            meta_raw = await self._run(
                _prop_get_dbus_send, bus, dest, IFACE_PLAYER, "Metadata"
            )
            metadata = _parse_metadata_dbus_send(meta_raw)

            try:
                st_raw = await self._run(
                    _prop_get_dbus_send, bus, dest, IFACE_PLAYER, "PlaybackStatus"
                )
                status = _parse_variant_string(st_raw) or "Stopped"
            except Exception:
                status = "Stopped"

            try:
                pos_raw = await self._run(
                    _prop_get_dbus_send, bus, dest, IFACE_PLAYER, "Position"
                )
                position = int(_parse_variant_number(pos_raw))
            except Exception:
                position = 0

            volume = 0.0
            can_volume = False
            try:
                vol_raw = await self._run(
                    _prop_get_dbus_send, bus, dest, IFACE_PLAYER, "Volume"
                )
                volume = float(_parse_variant_number(vol_raw))
                can_volume = True
            except Exception:
                pass

            can_seek = False
            try:
                sk_raw = await self._run(
                    _prop_get_dbus_send, bus, dest, IFACE_PLAYER, "CanSeek"
                )
                can_seek = _parse_variant_string(sk_raw).lower() in (
                    "true",
                    "1",
                ) or sk_raw.strip().endswith("true")
                if "boolean" in sk_raw and re.search(r"\btrue\b", sk_raw, re.I):
                    can_seek = True
            except Exception:
                pass

            try:
                id_raw = await self._run(
                    _prop_get_dbus_send, bus, dest, IFACE_ROOT, "Identity"
                )
                identity = _parse_variant_string(id_raw) or dest
            except Exception:
                identity = dest

            has_track = bool(
                metadata.get("title") or metadata.get("trackid") or metadata.get("artUrl")
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
                "busAddress": bus,
                "discoveryNote": self.last_note,
                "version": "2.0.3",
            }
        except Exception as e:
            self.last_error = str(e)
            _log_err(f"get_status: {e}\n{traceback.format_exc()}")
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
        except Exception as e:
            _log(f"set_position: {e}")
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
        except Exception as e:
            _log(f"set_volume: {e}")
            return False

    async def cache_album_art(self, art_url: str) -> str:
        if not art_url:
            return ""
        if not art_url.startswith("file:"):
            return art_url
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
        except Exception as e:
            _log(f"cache_album_art: {e}")
            return ""

    async def _call(self, method: str) -> bool:
        if not self.player:
            return False
        if not self.bus_address:
            _, addr, _ = await self._run(discover_players)
            self.bus_address = addr
        if not self.bus_address:
            return False
        try:
            await self._run(_player_call, self.bus_address, self.player, method)
            return True
        except Exception as e:
            _log(f"{method}: {e}")
            return False
