"""
main.py
=======

Decky Loader entry point for the MusicControl plugin.

How Decky uses this file
------------------------
1. Decky finds ``plugin.json`` next to this file, sees ``api_version: 1``.
2. It starts a sandboxed Python process and loads *this* file by absolute path.
3. It instantiates ``Plugin()`` (note: api_version >= 1 actually creates an
   instance — older legacy plugins received the class itself as ``self``).
4. It awaits ``Plugin._main()`` once at startup.
5. When the React UI calls ``callable("poll")()`` etc., Decky invokes the
   matching ``async def`` method on the instance with positional arguments.

Important import detail
-----------------------
Decky loads this file via ``importlib.util.spec_from_file_location``, which
does **not** put the plugin directory on ``sys.path``. Local modules like
``mpris_client`` would fail with ``ModuleNotFoundError`` unless we insert
``_plugin_dir`` ourselves (see below). This bug caused the "Backend not
responding" timeout in early 2.0.x builds.

Architecture (who does what)
----------------------------
* ``main.py`` (this file)  — Decky Plugin class, thin async wrappers
* ``mpris_client.py``      — caching MPRIS logic
* ``bus_discover.py``      — find the right session bus + run dbus-send
* ``mpris_parse.py``       — scrape dbus-send text into Python values
* ``settings_store.py``    — persist preferred player
* ``mpris_util.py``        — typed-metadata helpers used by unit tests

Threading note
--------------
All D-Bus work is blocking (subprocess). We run it in
``asyncio.to_thread(...)`` so Decky's event loop can still answer other
method calls and so a slow dbus-send cannot freeze the whole plugin.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Make sibling modules importable when Decky loads us by absolute path.
# ---------------------------------------------------------------------------
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

# ``decky`` is injected by the loader (also available as ``decky_plugin``
# for older plugins). It provides paths, logging, and migration helpers.
import decky  # type: ignore

from mpris_client import MprisClient
from settings_store import get_preferred_player, set_preferred_player


class Plugin:
    """
    The object Decky instantiates and calls into.

    Public async methods (no leading underscore) are the RPC surface
    callable from TypeScript via ``@decky/api``'s ``callable("name")``.
    """

    def __init__(self) -> None:
        # Shared MPRIS state (bus address, selected player, caches)
        self._client = MprisClient()

        # Absolute path of the last cover file we copied into the Steam UI
        # cache. Used so we can delete it when the track changes.
        self.previous_cached_image = ""

        # Directory for cover copies (under Decky's runtime data dir)
        self.cache_dir = ""

        # Symlink path under Steam's steamui/images/ so CEF can load covers
        self.symlink_path = ""

    async def _run(self, fn, *args, **kwargs):
        """
        Run a blocking function in a worker thread.

        Decky's plugin host is asyncio-based. If we called dbus-send
        directly on the event loop thread, a 2s timeout would stall every
        other RPC. ``to_thread`` keeps the loop responsive.
        """
        return await asyncio.to_thread(fn, *args, **kwargs)

    # ==================================================================
    # Lifecycle hooks (called by Decky, not by our UI)
    # ==================================================================

    async def _main(self) -> None:
        """
        One-time startup: prepare art cache + restore preferred player.

        Safe to fail partially — the plugin can still poll later even if
        the symlink setup fails (covers just won't show).
        """
        # Covers are copied here, then exposed to Steam via the symlink below
        self.cache_dir = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "cache")

        # Steam's built-in UI can load images from steamui/images/* via the
        # special host https://steamloopback.host/images/...
        self.symlink_path = os.path.join(
            decky.DECKY_USER_HOME,
            ".local/share/Steam/steamui/images/deckycache_musicControl",
        )

        # Start each session with an empty cover cache
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
        except Exception:
            pass
        os.makedirs(self.cache_dir, exist_ok=True)

        # Ensure the Steam UI can see our cache directory
        try:
            if not os.path.exists(self.symlink_path):
                os.makedirs(os.path.dirname(self.symlink_path), exist_ok=True)
                os.symlink(self.cache_dir, self.symlink_path, target_is_directory=True)
        except Exception:
            # Non-fatal: transport controls still work without art
            pass

        # Restore last user-selected player (may be offline right now)
        preferred = get_preferred_player()
        if preferred:
            self._client.player = preferred

        # Force a fresh discovery so logs show the real world at boot
        players = await self._run(self._client.list_players, True)
        decky.logger.info(
            f"MusicControl ready bus={self._client.bus_address!r} "
            f"players={len(players)} preferred={preferred!r}"
        )

    async def _unload(self) -> None:
        """Called when the plugin is stopped / reloaded. Nothing to clean up."""
        pass

    # ==================================================================
    # Primary RPC: poll() — one call per UI tick
    # ==================================================================

    async def poll(self) -> Dict[str, Any]:
        """
        Return everything the UI needs for one refresh frame.

        Shape::

            {
              "players": [ {"busName": "...", "identity": "Strawberry"}, ... ],
              "status":  { available, hasTrack, player, identity,
                           playbackStatus, position, volume,
                           canSeek, canControlVolume, metadata, error }
            }

        The frontend used to call list_players + get_status separately
        (and get_status used to issue many property Gets). Collapsing to
        one method cuts Decky IPC and D-Bus traffic dramatically.
        """
        try:
            # list_players uses the 3s TTL cache inside MprisClient
            players = await self._run(self._client.list_players, False)
            preferred = get_preferred_player()
            active = self._client.pick_player(preferred, players)
            if active and active != self._client.player:
                self._client.player = active

            if not players:
                # Nothing advertising MPRIS — UI shows empty state
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

    # ==================================================================
    # Secondary RPCs (still used by older UI paths / buttons)
    # ==================================================================

    async def list_players(self) -> List[Dict[str, str]]:
        """Return ``[{busName, identity}, ...]`` for the provider menu."""
        try:
            return await self._run(self._client.list_players, False)
        except Exception as e:
            decky.logger.error(f"list_players: {e}")
            return []

    async def set_player(self, player: str) -> str:
        """
        Select which MPRIS player subsequent commands control.

        Also persists the choice so the next Deck reboot / plugin reload
        prefers the same app when it is online.
        """
        self._client.player = player or ""
        set_preferred_player(self._client.player)
        # Expire the short-lived player-list cache so the next poll
        # re-reads identities / availability immediately
        self._client._players_cache_at = 0.0
        return self._client.player

    async def get_player(self) -> str:
        """Return the currently selected bus name (may be empty)."""
        return self._client.player

    async def get_status(self) -> Dict[str, Any]:
        """Status for the currently selected player only (no player list)."""
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
        """Toggle play/pause on the selected player. Returns success."""
        return await self._safe(lambda: self._client.call("PlayPause"))

    async def next_track(self) -> bool:
        """Skip to next track."""
        return await self._safe(lambda: self._client.call("Next"))

    async def previous_track(self) -> bool:
        """Skip to previous track."""
        return await self._safe(lambda: self._client.call("Previous"))

    async def set_position(self, position: int, track_id: str) -> bool:
        """
        Seek to ``position`` microseconds on ``track_id``.

        ``track_id`` must match the current track's mpris:trackid or the
        player will ignore the call (MPRIS rule).
        """
        return await self._safe(
            lambda: self._client.set_position(int(position), str(track_id))
        )

    async def set_volume(self, volume: float) -> bool:
        """Set volume in the range 0.0–1.0."""
        return await self._safe(lambda: self._client.set_volume(float(volume)))

    async def cache_album_art(self, art_url: str) -> str:
        """
        Prepare cover art for display in Steam UI.

        See ``MprisClient.cache_album_art`` for the symlink/steamloopback
        strategy. Returns a URL string suitable for ``<img src>``, or "".
        """
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
        """
        Run a blocking client mutator in a thread; return True/False only.

        UI buttons don't need error strings — they just need to know the
        click was attempted without killing the plugin process.
        """
        try:
            await self._run(fn)
            return True
        except Exception:
            return False
