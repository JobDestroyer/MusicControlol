"""
MusicControl backend — MPRIS control via jeepney (pure Python D-Bus),
with dbus-send fallback and multi-source session-bus discovery for SteamOS/Decky.
"""

from __future__ import annotations

import os
import pwd
import shutil
import subprocess
import sys
import traceback
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import unquote, urlparse

# Vendored pure-Python D-Bus client (py_modules/jeepney)
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
_py_modules = os.path.join(_plugin_dir, "py_modules")
if _py_modules not in sys.path:
    sys.path.insert(0, _py_modules)

import decky  # type: ignore
from jeepney import DBusAddress, Properties, new_method_call  # type: ignore
from jeepney.bus_messages import message_bus  # type: ignore
from jeepney.io.blocking import open_dbus_connection  # type: ignore
from jeepney.wrappers import DBusErrorResponse  # type: ignore

from mpris_util import metadata_to_dict, unwrap_variant

MPRIS_PREFIX = "org.mpris.MediaPlayer2"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
IFACE_ROOT = "org.mpris.MediaPlayer2"
IFACE_PLAYER = "org.mpris.MediaPlayer2.Player"

# Process name fragments whose /proc/*/environ often has the real Game Mode bus
_ENV_PROBE_PROCS = (
    "steam",
    "steamwebhelper",
    "gamescope",
    "strawberry",
    "plasmashell",
    "wireplumber",
    "pipewire",
)


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


def _session_uids() -> List[int]:
    """UIDs that might own a session bus on this machine."""
    uids: List[int] = []
    for getter in (
        lambda: os.getuid(),
        lambda: pwd.getpwnam(os.environ.get("DECKY_USER", "")).pw_uid,
        lambda: pwd.getpwnam(os.environ.get("USER", "")).pw_uid,
        lambda: pwd.getpwnam("deck").pw_uid,
    ):
        try:
            uid = int(getter())
            if uid not in uids and uid >= 1000:
                uids.append(uid)
        except Exception:
            pass
    # Any /run/user/* we can see
    try:
        for name in os.listdir("/run/user"):
            if name.isdigit():
                uid = int(name)
                if uid not in uids and uid >= 1000:
                    uids.append(uid)
    except Exception:
        pass
    return uids or [os.getuid()]


def _read_proc_environ(pid: int) -> Dict[str, str]:
    env: Dict[str, str] = {}
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            raw = f.read()
    except (OSError, PermissionError):
        return env
    for item in raw.split(b"\0"):
        if not item or b"=" not in item:
            continue
        k, v = item.split(b"=", 1)
        try:
            env[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
        except Exception:
            continue
    return env


def _proc_cmdline(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except Exception:
        return ""


def _addresses_from_processes() -> List[str]:
    """Pull DBUS_SESSION_BUS_ADDRESS from Steam / gamescope / player processes."""
    found: List[str] = []
    try:
        pids = [int(p) for p in os.listdir("/proc") if p.isdigit()]
    except Exception:
        return found

    for pid in pids:
        cmd = _proc_cmdline(pid).lower()
        if not cmd:
            continue
        if not any(tok in cmd for tok in _ENV_PROBE_PROCS):
            continue
        env = _read_proc_environ(pid)
        addr = env.get("DBUS_SESSION_BUS_ADDRESS")
        if addr and addr not in found:
            found.append(addr)
    return found


def _normalize_bus_address(addr: str) -> Optional[str]:
    """Return a jeepney-connectable address, or None if unusable."""
    if not addr:
        return None
    addr = addr.strip().strip('"').strip("'")
    # Prefer the first unix path in a multi-address list
    for part in addr.split(";"):
        part = part.strip()
        if part.startswith("unix:path="):
            path = part.split("=", 1)[1]
            # path may include extra ,guid=...
            path = path.split(",")[0]
            if os.path.exists(path):
                return f"unix:path={path}"
        if part.startswith("unix:abstract="):
            # jeepney supports abstract sockets
            return part.split(",")[0]
    # Bare filesystem path
    if addr.startswith("/") and os.path.exists(addr):
        return f"unix:path={addr}"
    return None


def _candidate_bus_addresses() -> List[str]:
    """Ordered unique list of session bus addresses to try."""
    raw: List[str] = []

    # 1) Addresses stolen from live session processes (best on Steam Deck Game Mode)
    raw.extend(_addresses_from_processes())

    # 2) Current environment (may be wrong inside Decky — still try)
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        raw.append(os.environ["DBUS_SESSION_BUS_ADDRESS"])

    # 3) systemctl --user show-environment (when user bus is reachable)
    for uid in _session_uids():
        try:
            out = subprocess.check_output(
                ["systemctl", "--user", "show-environment"],
                env={
                    **os.environ,
                    "XDG_RUNTIME_DIR": f"/run/user/{uid}",
                    "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{uid}/bus",
                },
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2,
            )
            for line in out.splitlines():
                if line.startswith("DBUS_SESSION_BUS_ADDRESS="):
                    raw.append(line.split("=", 1)[1].strip().strip('"'))
        except Exception:
            pass

    # 4) Conventional paths
    for uid in _session_uids():
        raw.append(f"unix:path=/run/user/{uid}/bus")
    xdg = os.environ.get("XDG_RUNTIME_DIR", "")
    if xdg:
        raw.append(f"unix:path={os.path.join(xdg, 'bus')}")

    # Normalize + dedupe, keep order
    out: List[str] = []
    for r in raw:
        n = _normalize_bus_address(r)
        if n and n not in out:
            out.append(n)
    return out


def _dbus_send_list_names(bus_addr: str) -> List[str]:
    """Fallback discovery using dbus-send (available on SteamOS)."""
    env = os.environ.copy()
    env["DBUS_SESSION_BUS_ADDRESS"] = bus_addr
    try:
        result = subprocess.check_output(
            [
                "dbus-send",
                "--session",
                "--print-reply",
                "--dest=org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus.ListNames",
            ],
            env=env,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3,
        )
    except Exception as e:
        raise RuntimeError(f"dbus-send ListNames failed: {e}") from e

    names: List[str] = []
    for line in result.splitlines():
        line = line.strip()
        # typical: string "org.mpris.MediaPlayer2.strawberry"
        if "string" in line and "org.mpris.MediaPlayer2" in line:
            # extract quoted name
            if '"' in line:
                name = line.split('"', 2)[1]
                if name.startswith(MPRIS_PREFIX):
                    names.append(name)
    return sorted(set(names))


def _jeepney_list_names(bus_addr: str) -> List[str]:
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_addr
    conn = open_dbus_connection(bus="SESSION")
    try:
        reply = conn.send_and_get_reply(message_bus.ListNames(), timeout=3.0)
        names = reply.body[0]
        return sorted(n for n in names if isinstance(n, str) and n.startswith(MPRIS_PREFIX))
    finally:
        try:
            conn.close()
        except Exception:
            pass


def discover_mpris_players() -> Tuple[List[str], str, str]:
    """
    Try each candidate bus; return (mpris_names, bus_address_used, note).
    Prefers a bus that actually has MPRIS names.
    """
    candidates = _candidate_bus_addresses()
    if not candidates:
        return [], "", "no session bus candidates found"

    notes: List[str] = []
    empty_ok_bus = ""  # bus that answers but has zero MPRIS

    for addr in candidates:
        # Try jeepney first
        try:
            names = _jeepney_list_names(addr)
            if names:
                return names, addr, f"jeepney ok; candidates={len(candidates)}"
            empty_ok_bus = empty_ok_bus or addr
            notes.append(f"{addr}: jeepney 0 players")
        except Exception as e:
            notes.append(f"{addr}: jeepney err {e}")

        # dbus-send fallback on same address
        try:
            names = _dbus_send_list_names(addr)
            if names:
                return names, addr, f"dbus-send ok; candidates={len(candidates)}"
            empty_ok_bus = empty_ok_bus or addr
            notes.append(f"{addr}: dbus-send 0 players")
        except Exception as e:
            notes.append(f"{addr}: dbus-send err {e}")

    # Connected somewhere but no MPRIS — still bind that bus for later
    if empty_ok_bus:
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = empty_ok_bus
        return [], empty_ok_bus, "bus ok but no MPRIS names; " + " | ".join(notes[-6:])

    return [], "", "all bus candidates failed; " + " | ".join(notes[-8:])


class MprisClient:
    """Thin synchronous MPRIS client (called from async plugin methods)."""

    def __init__(self) -> None:
        self._conn = None
        self.bus_address: str = ""
        self.last_discovery_note: str = ""

    def refresh_bus(self, force: bool = False) -> None:
        """Pick / re-pick a working session bus."""
        if self.bus_address and not force and os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
            return
        names, addr, note = discover_mpris_players()
        self.last_discovery_note = note
        if addr:
            self.bus_address = addr
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
            self.close()  # reconnect on next use
        _log(f"bus discovery: addr={addr!r} players={names} note={note}")

    def _connect(self):
        self.refresh_bus(force=False)
        if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
            # last resort
            for addr in _candidate_bus_addresses():
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
                break
        if self._conn is None:
            self._conn = open_dbus_connection(bus="SESSION")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _send(self, msg, timeout: float = 2.0):
        conn = self._connect()
        try:
            return conn.send_and_get_reply(msg, timeout=timeout)
        except Exception:
            self.close()
            conn = self._connect()
            return conn.send_and_get_reply(msg, timeout=timeout)

    def _player_addr(self, bus_name: str) -> DBusAddress:
        return DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=IFACE_PLAYER)

    def list_names(self, force_rediscover: bool = True) -> List[str]:
        # Always rediscover on list — cheap and handles Strawberry starting later
        names, addr, note = discover_mpris_players()
        self.last_discovery_note = note
        if addr:
            if addr != self.bus_address:
                self.bus_address = addr
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
                self.close()
            else:
                os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr
        return names

    def get_property(self, bus_name: str, interface: str, name: str) -> Any:
        addr = DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=interface)
        reply = self._send(Properties(addr).get(name))
        return unwrap_variant(reply.body[0])

    def set_property(
        self, bus_name: str, interface: str, name: str, signature: str, value: Any
    ) -> None:
        addr = DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=interface)
        self._send(Properties(addr).set(name, signature, value))

    def call_player(
        self, bus_name: str, method: str, signature: str = "", body: Tuple = ()
    ) -> Any:
        addr = self._player_addr(bus_name)
        msg = new_method_call(addr, method, signature or None, body)
        reply = self._send(msg)
        return reply.body

    def identity(self, bus_name: str) -> str:
        try:
            val = self.get_property(bus_name, IFACE_ROOT, "Identity")
            return str(val) if val else bus_name.replace(MPRIS_PREFIX + ".", "")
        except Exception:
            return bus_name.replace(MPRIS_PREFIX + ".", "")

    def dbus_send_call(self, bus_name: str, method: str) -> bool:
        """Fire-and-forget player method via dbus-send (no args)."""
        if not self.bus_address:
            self.refresh_bus(force=True)
        env = os.environ.copy()
        if self.bus_address:
            env["DBUS_SESSION_BUS_ADDRESS"] = self.bus_address
        try:
            subprocess.check_call(
                [
                    "dbus-send",
                    "--session",
                    "--print-reply",
                    f"--dest={bus_name}",
                    MPRIS_PATH,
                    f"{IFACE_PLAYER}.{method}",
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return True
        except Exception as e:
            _log_err(f"dbus-send {method} failed: {e}")
            return False


class Plugin:
    player: str = ""
    previous_cached_image: str = ""
    cache_dir: str = ""
    symlink_path: str = ""

    def __init__(self) -> None:
        self.player = ""
        self.previous_cached_image = ""
        self.cache_dir = ""
        self.symlink_path = ""
        self._mpris = MprisClient()
        self._last_error = ""

    async def _main(self) -> None:
        self.cache_dir = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "cache")
        self.symlink_path = os.path.join(
            decky.DECKY_USER_HOME,
            ".local/share/Steam/steamui/images/deckycache_musicControl",
        )
        self.previous_cached_image = ""
        self.player = ""

        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
        except Exception as e:
            _log(f"Failed to clear cache folder: {e}")

        os.makedirs(self.cache_dir, exist_ok=True)

        try:
            if not os.path.exists(self.symlink_path):
                parent = os.path.dirname(self.symlink_path)
                os.makedirs(parent, exist_ok=True)
                os.symlink(self.cache_dir, self.symlink_path, target_is_directory=True)
        except Exception as e:
            _log(f"Failed to create art symlink: {e}")

        # Probe bus at startup
        names = self._mpris.list_names()
        _log(
            f"ready uid={os.getuid()} decky_user={os.environ.get('DECKY_USER')} "
            f"bus={self._mpris.bus_address!r} mpris={names} "
            f"note={self._mpris.last_discovery_note}"
        )

    async def _unload(self) -> None:
        self._mpris.close()
        _log("unloaded")

    async def debug_info(self) -> Dict[str, Any]:
        """Diagnostics for the UI / logs when discovery fails."""
        names: List[str] = []
        try:
            names = self._mpris.list_names()
        except Exception as e:
            self._last_error = str(e)
        return {
            "uid": os.getuid(),
            "deckyUser": os.environ.get("DECKY_USER", ""),
            "busAddress": self._mpris.bus_address
            or os.environ.get("DBUS_SESSION_BUS_ADDRESS", ""),
            "candidates": _candidate_bus_addresses(),
            "players": names,
            "note": self._mpris.last_discovery_note,
            "error": self._last_error,
            "dbusSend": shutil.which("dbus-send") or "",
        }

    async def list_players(self) -> List[Dict[str, str]]:
        try:
            names = self._mpris.list_names()
            self._last_error = ""
        except Exception as e:
            self._last_error = str(e)
            _log_err(f"list_players failed: {e}\n{traceback.format_exc()}")
            return []

        players: List[Dict[str, str]] = []
        for name in names:
            try:
                identity = self._mpris.identity(name)
            except Exception:
                identity = name.replace(MPRIS_PREFIX + ".", "")
            players.append({"busName": name, "identity": identity})
        if not players and self._mpris.last_discovery_note:
            self._last_error = self._mpris.last_discovery_note
        return players

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
            "error": self._last_error or "",
            "busAddress": self._mpris.bus_address,
            "discoveryNote": self._mpris.last_discovery_note,
        }

        if not self.player:
            try:
                names = self._mpris.list_names()
            except Exception as e:
                empty["error"] = f"dbus: {e}"
                return empty
            if not names:
                empty["error"] = (
                    self._mpris.last_discovery_note
                    or "No MPRIS players on session bus. Is Strawberry running from Game Mode?"
                )
                return empty
            self.player = names[0]

        try:
            meta_raw = self._mpris.get_property(self.player, IFACE_PLAYER, "Metadata")
            metadata = metadata_to_dict(meta_raw)

            try:
                status = str(
                    self._mpris.get_property(self.player, IFACE_PLAYER, "PlaybackStatus")
                )
            except Exception:
                status = "Stopped"

            try:
                position = int(
                    self._mpris.get_property(self.player, IFACE_PLAYER, "Position") or 0
                )
            except Exception:
                position = 0

            volume = 0.0
            can_volume = False
            try:
                volume = float(
                    self._mpris.get_property(self.player, IFACE_PLAYER, "Volume")
                )
                can_volume = True
            except Exception:
                can_volume = False

            try:
                can_seek = bool(
                    self._mpris.get_property(self.player, IFACE_PLAYER, "CanSeek")
                )
            except Exception:
                can_seek = False

            try:
                identity = self._mpris.identity(self.player)
            except Exception:
                identity = self.player

            has_track = bool(
                metadata.get("title") or metadata.get("trackid") or metadata.get("artUrl")
            )

            return {
                "available": True,
                "hasTrack": has_track,
                "player": self.player,
                "identity": identity,
                "playbackStatus": status,
                "position": position,
                "volume": volume,
                "canSeek": can_seek,
                "canControlVolume": can_volume,
                "metadata": metadata,
                "error": "",
                "busAddress": self._mpris.bus_address,
                "discoveryNote": self._mpris.last_discovery_note,
            }
        except DBusErrorResponse as e:
            _log(f"get_status DBus error for {self.player}: {e.name} {e.data}")
            empty["player"] = self.player
            empty["error"] = f"{e.name}"
            self.player = ""
            return empty
        except Exception as e:
            _log_err(f"get_status failed: {e}\n{traceback.format_exc()}")
            # One rediscovery + retry path for stale bus
            try:
                self._mpris.close()
                self._mpris.refresh_bus(force=True)
            except Exception:
                pass
            empty["error"] = str(e)
            return empty

    async def play_pause(self) -> bool:
        return self._safe_call("PlayPause")

    async def next_track(self) -> bool:
        return self._safe_call("Next")

    async def previous_track(self) -> bool:
        return self._safe_call("Previous")

    async def set_position(self, position: int, track_id: str) -> bool:
        if not self.player or not track_id:
            return False
        try:
            self._mpris.call_player(
                self.player, "SetPosition", "ox", (str(track_id), int(position))
            )
            return True
        except Exception as e:
            _log(f"set_position failed: {e}")
            return False

    async def set_volume(self, volume: float) -> bool:
        if not self.player:
            return False
        try:
            volume = max(0.0, min(1.0, float(volume)))
            self._mpris.set_property(self.player, IFACE_PLAYER, "Volume", "d", volume)
            return True
        except Exception as e:
            _log(f"set_volume failed: {e}")
            return False

    async def cache_album_art(self, art_url: str) -> str:
        if not art_url:
            return ""
        if not art_url.startswith("file:"):
            return art_url

        try:
            parsed = urlparse(art_url)
            path = unquote(parsed.path)
            if not path or not os.path.exists(path):
                return ""

            if self.previous_cached_image and os.path.exists(self.previous_cached_image):
                try:
                    os.remove(self.previous_cached_image)
                except Exception:
                    pass
                self.previous_cached_image = ""

            base = os.path.basename(path) or "cover.jpg"
            stem, ext = os.path.splitext(base)
            safe = f"{stem}_{abs(hash(path)) & 0xFFFFFFFF:x}{ext or '.jpg'}"
            target = os.path.join(self.cache_dir, safe)
            shutil.copy2(path, target)
            self.previous_cached_image = target
            return f"https://steamloopback.host/images/deckycache_musicControl/{safe}"
        except Exception as e:
            _log(f"cache_album_art failed: {e}")
            return ""

    def _safe_call(self, method: str) -> bool:
        if not self.player:
            return False
        try:
            self._mpris.call_player(self.player, method)
            return True
        except Exception as e:
            _log(f"jeepney {method} failed: {e}; trying dbus-send")
            return self._mpris.dbus_send_call(self.player, method)
