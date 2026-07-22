"""
MusicControl backend — MPRIS control via jeepney (pure Python D-Bus).

Supports any org.mpris.MediaPlayer2.* player on the session bus, including
Strawberry, Spotify, and Firefox Flatpak.
"""

from __future__ import annotations

import os
import shutil
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple
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


def _ensure_session_bus_env() -> None:
    """Point jeepney at the host user's session bus (Decky sandbox often lacks this)."""
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        return
    uid = os.getuid()
    path = f"/run/user/{uid}/bus"
    if os.path.exists(path):
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={path}"
        return
    # Fallbacks used on some SteamOS / gamescope setups
    xdg = os.environ.get("XDG_RUNTIME_DIR", "")
    if xdg:
        bus = os.path.join(xdg, "bus")
        if os.path.exists(bus):
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"



class MprisClient:
    """Thin synchronous MPRIS client (called from async plugin methods)."""

    def __init__(self) -> None:
        self._conn = None

    def _connect(self):
        _ensure_session_bus_env()
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
            reply = conn.send_and_get_reply(msg, timeout=timeout)
            return reply
        except Exception:
            # Drop dead connection and retry once
            self.close()
            conn = self._connect()
            return conn.send_and_get_reply(msg, timeout=timeout)

    def _player_addr(self, bus_name: str) -> DBusAddress:
        return DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=IFACE_PLAYER)

    def _root_addr(self, bus_name: str) -> DBusAddress:
        return DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=IFACE_ROOT)

    def list_names(self) -> List[str]:
        reply = self._send(message_bus.ListNames())
        names = reply.body[0]
        return sorted(n for n in names if n.startswith(MPRIS_PREFIX))

    def get_property(self, bus_name: str, interface: str, name: str) -> Any:
        addr = DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=interface)
        reply = self._send(Properties(addr).get(name))
        # Get returns a single variant
        return unwrap_variant(reply.body[0])

    def set_property(self, bus_name: str, interface: str, name: str, signature: str, value: Any) -> None:
        addr = DBusAddress(MPRIS_PATH, bus_name=bus_name, interface=interface)
        self._send(Properties(addr).set(name, signature, value))

    def call_player(self, bus_name: str, method: str, signature: str = "", body: Tuple = ()) -> Any:
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

    # ---- lifecycle ----

    async def _main(self) -> None:
        _ensure_session_bus_env()
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
            decky.logger.warning(f"Failed to clear cache folder: {e}")

        os.makedirs(self.cache_dir, exist_ok=True)

        try:
            if not os.path.exists(self.symlink_path):
                parent = os.path.dirname(self.symlink_path)
                os.makedirs(parent, exist_ok=True)
                os.symlink(self.cache_dir, self.symlink_path, target_is_directory=True)
        except Exception as e:
            decky.logger.warning(f"Failed to create art symlink: {e}")

        decky.logger.info(
            f"MusicControl ready uid={os.getuid()} bus={os.environ.get('DBUS_SESSION_BUS_ADDRESS')}"
        )

    async def _unload(self) -> None:
        self._mpris.close()
        decky.logger.info("MusicControl unloaded")

    # ---- public API (api_version 1: normal instance methods, positional args) ----

    async def list_players(self) -> List[Dict[str, str]]:
        """Return [{busName, identity}, ...] for active MPRIS players."""
        try:
            names = self._mpris.list_names()
        except Exception as e:
            decky.logger.error(f"list_players failed: {e}\n{traceback.format_exc()}")
            return []

        players: List[Dict[str, str]] = []
        for name in names:
            players.append({"busName": name, "identity": self._mpris.identity(name)})
        return players

    async def set_player(self, player: str) -> str:
        self.player = player or ""
        return self.player

    async def get_player(self) -> str:
        return self.player

    async def get_status(self) -> Dict[str, Any]:
        """
        Single poll snapshot for the UI.
        {
          available, player, identity, playbackStatus, position, volume,
          canSeek, canControlVolume, metadata: {title, artist, artUrl, length, trackid, ...}
        }
        """
        empty: Dict[str, Any] = {
            "available": False,
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

        if not self.player:
            # Auto-select first available player
            try:
                names = self._mpris.list_names()
            except Exception as e:
                empty["error"] = f"dbus: {e}"
                return empty
            if not names:
                return empty
            self.player = names[0]

        try:
            meta_raw = self._mpris.get_property(self.player, IFACE_PLAYER, "Metadata")
            metadata = metadata_to_dict(meta_raw)

            try:
                status = str(self._mpris.get_property(self.player, IFACE_PLAYER, "PlaybackStatus"))
            except Exception:
                status = "Stopped"

            try:
                position = int(self._mpris.get_property(self.player, IFACE_PLAYER, "Position") or 0)
            except Exception:
                position = 0

            volume = 0.0
            can_volume = False
            try:
                volume = float(self._mpris.get_property(self.player, IFACE_PLAYER, "Volume"))
                can_volume = True
            except Exception:
                can_volume = False

            try:
                can_seek = bool(self._mpris.get_property(self.player, IFACE_PLAYER, "CanSeek"))
            except Exception:
                can_seek = False

            try:
                identity = self._mpris.identity(self.player)
            except Exception:
                identity = self.player

            has_track = bool(metadata.get("title") or metadata.get("trackid") or metadata.get("artUrl"))

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
            }
        except DBusErrorResponse as e:
            decky.logger.warning(f"get_status DBus error for {self.player}: {e.name} {e.data}")
            empty["player"] = self.player
            empty["error"] = f"{e.name}"
            # Player may have vanished
            self.player = ""
            return empty
        except Exception as e:
            decky.logger.error(f"get_status failed: {e}\n{traceback.format_exc()}")
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
            # MPRIS SetPosition(o trackId, x position)
            self._mpris.call_player(
                self.player, "SetPosition", "ox", (str(track_id), int(position))
            )
            return True
        except Exception as e:
            decky.logger.warning(f"set_position failed: {e}")
            return False

    async def set_volume(self, volume: float) -> bool:
        if not self.player:
            return False
        try:
            volume = max(0.0, min(1.0, float(volume)))
            self._mpris.set_property(self.player, IFACE_PLAYER, "Volume", "d", volume)
            return True
        except Exception as e:
            decky.logger.warning(f"set_volume failed: {e}")
            return False

    async def cache_album_art(self, art_url: str) -> str:
        """
        Copy file:// cover art into Steam UI-reachable cache.
        Returns https://steamloopback.host/... URL or original remote URL or "".
        """
        if not art_url:
            return ""
        if not art_url.startswith("file:"):
            return art_url

        try:
            parsed = urlparse(art_url)
            # file:///path → /path (handle + decode)
            path = unquote(parsed.path)
            if not path or not os.path.exists(path):
                decky.logger.debug(f"art path missing: {path}")
                return ""

            if self.previous_cached_image and os.path.exists(self.previous_cached_image):
                try:
                    os.remove(self.previous_cached_image)
                except Exception:
                    pass
                self.previous_cached_image = ""

            base = os.path.basename(path) or "cover.jpg"
            # Avoid collisions across albums with same filename
            stem, ext = os.path.splitext(base)
            safe = f"{stem}_{abs(hash(path)) & 0xFFFFFFFF:x}{ext or '.jpg'}"
            target = os.path.join(self.cache_dir, safe)
            shutil.copy2(path, target)
            self.previous_cached_image = target
            return f"https://steamloopback.host/images/deckycache_musicControl/{safe}"
        except Exception as e:
            decky.logger.warning(f"cache_album_art failed: {e}")
            return ""

    def _safe_call(self, method: str) -> bool:
        if not self.player:
            return False
        try:
            self._mpris.call_player(self.player, method)
            return True
        except Exception as e:
            decky.logger.warning(f"{method} failed: {e}")
            return False
