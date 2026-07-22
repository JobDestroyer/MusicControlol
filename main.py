"""
MusicControl — Decky plugin backend (MPRIS over session D-Bus).
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from typing import Any, Dict, List

_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

import decky  # type: ignore

from mpris_client import MprisClient
from settings_store import get_preferred_player, set_preferred_player


class Plugin:
    def __init__(self) -> None:
        self._client = MprisClient()
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

        preferred = get_preferred_player()
        if preferred:
            self._client.player = preferred

        players = await self._run(self._client.list_players, True)
        decky.logger.info(
            f"MusicControl ready bus={self._client.bus_address!r} "
            f"players={len(players)} preferred={preferred!r}"
        )

    async def _unload(self) -> None:
        pass

    # ---- primary API ----

    async def poll(self) -> Dict[str, Any]:
        """
        Single snapshot for the UI: players list + active player status.
        """
        try:
            players = await self._run(self._client.list_players, False)
            preferred = get_preferred_player()
            active = self._client.pick_player(preferred, players)
            if active and active != self._client.player:
                self._client.player = active

            if not players:
                return {
                    "players": [],
                    "status": {
                        "available": False,
                        "hasTrack": False,
                        "player": "",
                        "identity": "",
                        "playbackStatus": "Stopped",
                        "position": 0,
                        "volume": 0.0,
                        "canSeek": False,
                        "canControlVolume": False,
                        "metadata": {},
                        "error": "",
                    },
                }

            status = await self._run(self._client.get_status, active)
            return {"players": players, "status": status}
        except Exception as e:
            decky.logger.error(f"poll: {e}")
            return {
                "players": [],
                "status": {
                    "available": False,
                    "hasTrack": False,
                    "player": self._client.player,
                    "identity": "",
                    "playbackStatus": "Stopped",
                    "position": 0,
                    "volume": 0.0,
                    "canSeek": False,
                    "canControlVolume": False,
                    "metadata": {},
                    "error": str(e),
                },
            }

    async def list_players(self) -> List[Dict[str, str]]:
        try:
            return await self._run(self._client.list_players, False)
        except Exception as e:
            decky.logger.error(f"list_players: {e}")
            return []

    async def set_player(self, player: str) -> str:
        self._client.player = player or ""
        set_preferred_player(self._client.player)
        # invalidate sticky list so next poll reflects choice immediately
        self._client._players_cache_at = 0.0
        return self._client.player

    async def get_player(self) -> str:
        return self._client.player

    async def get_status(self) -> Dict[str, Any]:
        try:
            return await self._run(self._client.get_status, None)
        except Exception as e:
            decky.logger.error(f"get_status: {e}")
            return {
                "available": False,
                "hasTrack": False,
                "player": self._client.player,
                "identity": "",
                "playbackStatus": "Stopped",
                "position": 0,
                "volume": 0.0,
                "canSeek": False,
                "canControlVolume": False,
                "metadata": {},
                "error": str(e),
            }

    async def play_pause(self) -> bool:
        return await self._safe(lambda: self._client.call("PlayPause"))

    async def next_track(self) -> bool:
        return await self._safe(lambda: self._client.call("Next"))

    async def previous_track(self) -> bool:
        return await self._safe(lambda: self._client.call("Previous"))

    async def set_position(self, position: int, track_id: str) -> bool:
        return await self._safe(
            lambda: self._client.set_position(int(position), str(track_id))
        )

    async def set_volume(self, volume: float) -> bool:
        return await self._safe(lambda: self._client.set_volume(float(volume)))

    async def cache_album_art(self, art_url: str) -> str:
        try:
            url, prev = await self._run(
                self._client.cache_album_art,
                art_url,
                self.cache_dir,
                self.previous_cached_image,
            )
            self.previous_cached_image = prev
            return url
        except Exception:
            return ""

    async def _safe(self, fn) -> bool:
        try:
            await self._run(fn)
            return True
        except Exception:
            return False
