"""
mpris_client.py
===============

Purpose
-------
High-level **MPRIS client** used by the Decky plugin.

This is the layer that:

* Remembers which session bus we successfully talked to (with a TTL).
* Remembers the list of media players (with a shorter TTL).
* Remembers friendly "Identity" strings so we don't re-query every second.
* Implements play/pause/next/previous, seek, volume, and album-art caching.
* Builds the status dict the React UI consumes.

Transport
---------
All actual D-Bus traffic goes through ``bus_discover.run_dbus_send``
(which shells out to ``dbus-send``). Parsing of replies is in
``mpris_parse.py``.

Caching philosophy
------------------
The UI calls ``poll()`` about once per second while the Quick Access menu
is open. Without caching we would:

* Re-scan bus candidates every tick
* ``ListNames`` every tick
* Fetch Identity for every player every tick
* Fetch 5 properties individually every tick

With caching we:

* Stick to a working bus for ~60s (``BUS_STICKY_SEC``)
* Reuse the player list for ~3s (``PLAYERS_TTL_SEC``)
* Prefer one ``Properties.GetAll`` per status tick

MPRIS object paths / interfaces (fixed by the MPRIS 2.2 spec)
------------------------------------------------------------
* Object path: ``/org/mpris/MediaPlayer2``  (always)
* Root iface:  ``org.mpris.MediaPlayer2``   (Identity, Raise, Quit, …)
* Player iface:``org.mpris.MediaPlayer2.Player`` (PlayPause, Metadata, …)
"""

from __future__ import annotations

import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

from bus_discover import (
    discover_players,
    list_mpris_names,
    run_dbus_send,
)
from mpris_parse import (
    identity_from_bus_name,
    parse_metadata,
    parse_player_get_all,
    parse_variant_bool,
    parse_variant_number,
    parse_variant_string,
)

# ---------------------------------------------------------------------------
# Spec-mandated constants (do not change unless the MPRIS spec changes)
# ---------------------------------------------------------------------------

# Every MPRIS player exports its objects at this single path
MPRIS_PATH = "/org/mpris/MediaPlayer2"

# Root interface: app-level info (name, can-raise, etc.)
IFACE_ROOT = "org.mpris.MediaPlayer2"

# Player interface: transport controls and track metadata
IFACE_PLAYER = "org.mpris.MediaPlayer2.Player"

# ---------------------------------------------------------------------------
# Cache TTLs (seconds). Tuned for a 1 Hz UI poll without thrashing D-Bus.
# ---------------------------------------------------------------------------

# How long to trust the last successful ListNames / player list
PLAYERS_TTL_SEC = 3.0

# How long to keep using a bus address that worked, before re-probing
# all candidates from scratch
BUS_STICKY_SEC = 60.0


class MprisClient:
    """
    Stateful MPRIS helper.

    One instance lives for the lifetime of the Decky plugin process
    (created in ``Plugin.__init__``).
    """

    def __init__(self) -> None:
        # Last known-good session bus address (``unix:path=...``)
        self.bus_address: str = ""

        # Currently selected player well-known name
        # e.g. "org.mpris.MediaPlayer2.strawberry"
        self.player: str = ""

        # Cached list of {"busName", "identity"} dicts for the UI picker
        self._players_cache: List[Dict[str, str]] = []
        # Monotonic timestamp when _players_cache was filled
        self._players_cache_at: float = 0.0

        # Monotonic timestamp when bus_address was last confirmed working
        self._bus_ok_at: float = 0.0

        # busName → Identity string (e.g. "Strawberry") so we don't re-Get
        self._identity_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Bus selection
    # ------------------------------------------------------------------

    def _set_bus(self, addr: str) -> None:
        """
        Remember a working bus address and export it into the environment.

        Setting ``DBUS_SESSION_BUS_ADDRESS`` helps any subsequent child
        process (or library) pick the same bus by default.
        """
        if not addr:
            return
        self.bus_address = addr
        self._bus_ok_at = time.monotonic()
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr

    def ensure_bus(self, force: bool = False) -> str:
        """
        Return a session bus address, discovering one if needed.

        If we already have an address younger than ``BUS_STICKY_SEC`` and
        ``force`` is False, reuse it without scanning candidates again.
        """
        now = time.monotonic()
        if (
            not force
            and self.bus_address
            and now - self._bus_ok_at < BUS_STICKY_SEC
        ):
            return self.bus_address

        # Full candidate scan (may return names + addr, or empty names + addr)
        names, addr = discover_players()
        if addr:
            self._set_bus(addr)
            # If discovery already listed players, seed the short-lived cache
            if names:
                self._players_cache = self._names_to_players(names, addr)
                self._players_cache_at = now
        return self.bus_address

    # ------------------------------------------------------------------
    # Player enumeration
    # ------------------------------------------------------------------

    def _names_to_players(self, names: List[str], bus: str) -> List[Dict[str, str]]:
        """
        Convert raw bus names into UI rows: ``{busName, identity}``.

        ``identity`` is the MPRIS Identity property ("Strawberry") when
        available, otherwise a stripped form of the bus name.
        """
        players: List[Dict[str, str]] = []
        for name in names:
            identity = self._identity_cache.get(name)
            if not identity:
                # Default label from the bus name itself
                identity = identity_from_bus_name(name)
                try:
                    # Ask the player for its official Identity string
                    raw = run_dbus_send(
                        bus,
                        [
                            f"--dest={name}",
                            MPRIS_PATH,
                            "org.freedesktop.DBus.Properties.Get",
                            f"string:{IFACE_ROOT}",
                            "string:Identity",
                        ],
                        timeout=1.5,
                    )
                    identity = parse_variant_string(raw) or identity
                except Exception:
                    # Player may not implement Identity — keep fallback
                    pass
                self._identity_cache[name] = identity
            players.append({"busName": name, "identity": identity})
        return players

    def list_players(self, force: bool = False) -> List[Dict[str, str]]:
        """
        Return the list of controllable MPRIS players.

        Uses a short TTL cache unless ``force`` is True (used at plugin
        startup so we don't show a stale empty list after load).
        """
        now = time.monotonic()

        # Fast path: recent cache still valid
        if (
            not force
            and self._players_cache
            and now - self._players_cache_at < PLAYERS_TTL_SEC
        ):
            return list(self._players_cache)

        bus = self.ensure_bus(force=force)
        if not bus:
            # ensure_bus found nothing sticky — try a full discover once more
            names, addr = discover_players()
            if addr:
                self._set_bus(addr)
                bus = addr
                players = self._names_to_players(names, bus)
                self._players_cache = players
                self._players_cache_at = now
                return list(players)
            self._players_cache = []
            self._players_cache_at = now
            return []

        # We have a bus: just re-list names on it (cheap)
        try:
            names = list_mpris_names(bus)
        except Exception:
            # Sticky bus may have died (user switched modes, etc.)
            names, addr = discover_players()
            if not addr:
                self._players_cache = []
                self._players_cache_at = now
                return []
            self._set_bus(addr)
            bus = addr
            # ``names`` already set by discover_players

        players = self._names_to_players(names, bus)
        self._players_cache = players
        self._players_cache_at = now

        # Drop identity entries for players that disappeared
        live = {p["busName"] for p in players}
        self._identity_cache = {
            k: v for k, v in self._identity_cache.items() if k in live
        }
        return list(players)

    def pick_player(self, preferred: str, players: List[Dict[str, str]]) -> str:
        """
        Choose which player to control.

        Priority:
          1. ``preferred`` if still online (user's last explicit choice)
          2. Currently selected ``self.player`` if still online
          3. First entry in the list (stable sort from ListNames)
          4. Empty string if nothing is available
        """
        names = [p["busName"] for p in players]
        if not names:
            return ""
        if preferred and preferred in names:
            return preferred
        if self.player and self.player in names:
            return self.player
        return names[0]

    # ------------------------------------------------------------------
    # Status (what track is playing, where, volume, …)
    # ------------------------------------------------------------------

    def get_status(self, dest: Optional[str] = None) -> Dict[str, Any]:
        """
        Build the status object for one player.

        Parameters
        ----------
        dest:
            Bus name to query. Defaults to ``self.player``.

        Returns a dict always containing the keys the frontend expects,
        even on failure (``available: False``).
        """
        empty: Dict[str, Any] = {
            "available": False,
            "hasTrack": False,
            "player": dest or self.player,
            "identity": "",
            "playbackStatus": "Stopped",
            "position": 0,  # microseconds
            "volume": 0.0,  # 0.0 – 1.0
            "canSeek": False,
            "canControlVolume": False,
            "metadata": {},
            "error": "",
        }
        bus = self.ensure_bus()
        player = dest or self.player
        if not bus or not player:
            return empty

        # Prefer one GetAll call (all Player properties in a single round-trip)
        try:
            raw = run_dbus_send(
                bus,
                [
                    f"--dest={player}",
                    MPRIS_PATH,
                    "org.freedesktop.DBus.Properties.GetAll",
                    f"string:{IFACE_PLAYER}",
                ],
                timeout=2.0,
            )
            parsed = parse_player_get_all(raw)
        except Exception:
            # Some players misbehave on GetAll — fall back to individual Gets
            try:
                parsed = self._status_via_individual_gets(bus, player)
            except Exception as e:
                empty["error"] = str(e)
                return empty

        meta = parsed.get("metadata") or {}

        # Resolve friendly Identity (cached when possible)
        identity = self._identity_cache.get(player) or identity_from_bus_name(player)
        try:
            if player not in self._identity_cache:
                id_raw = run_dbus_send(
                    bus,
                    [
                        f"--dest={player}",
                        MPRIS_PATH,
                        "org.freedesktop.DBus.Properties.Get",
                        f"string:{IFACE_ROOT}",
                        "string:Identity",
                    ],
                    timeout=1.5,
                )
                identity = parse_variant_string(id_raw) or identity
                self._identity_cache[player] = identity
            else:
                identity = self._identity_cache[player]
        except Exception:
            pass

        # "Has a track" = any of title / trackid / art is present
        has_track = bool(
            meta.get("title") or meta.get("trackid") or meta.get("artUrl")
        )
        return {
            "available": True,
            "hasTrack": has_track,
            "player": player,
            "identity": identity,
            "playbackStatus": parsed.get("playbackStatus") or "Stopped",
            "position": int(parsed.get("position") or 0),
            "volume": float(parsed.get("volume") or 0.0),
            "canSeek": bool(parsed.get("canSeek")),
            "canControlVolume": bool(parsed.get("canControlVolume")),
            "metadata": meta,
            "error": "",
        }

    def _status_via_individual_gets(self, bus: str, player: str) -> Dict[str, Any]:
        """
        Fallback status fetch: one Properties.Get per field.

        Slower than GetAll but works with pickier MPRIS implementations.
        """

        def prop(name: str) -> str:
            return run_dbus_send(
                bus,
                [
                    f"--dest={player}",
                    MPRIS_PATH,
                    "org.freedesktop.DBus.Properties.Get",
                    f"string:{IFACE_PLAYER}",
                    f"string:{name}",
                ],
                timeout=1.5,
            )

        meta = parse_metadata(prop("Metadata"))
        status = parse_variant_string(prop("PlaybackStatus")) or "Stopped"
        try:
            position = int(parse_variant_number(prop("Position")))
        except Exception:
            position = 0
        volume = 0.0
        can_volume = False
        try:
            volume = float(parse_variant_number(prop("Volume")))
            can_volume = True
        except Exception:
            # Many players expose Volume as read-only or not at all
            pass
        can_seek = False
        try:
            can_seek = parse_variant_bool(prop("CanSeek"))
        except Exception:
            pass
        return {
            "playbackStatus": status,
            "position": position,
            "volume": volume,
            "canSeek": can_seek,
            "canControlVolume": can_volume,
            "metadata": meta,
        }

    # ------------------------------------------------------------------
    # Transport controls
    # ------------------------------------------------------------------

    def call(self, method: str) -> None:
        """
        Invoke a no-argument Player method (PlayPause, Next, Previous, …).

        Raises RuntimeError if no bus/player is selected.
        """
        bus = self.ensure_bus()
        if not bus or not self.player:
            raise RuntimeError("no player")
        run_dbus_send(
            bus,
            [
                f"--dest={self.player}",
                MPRIS_PATH,
                f"{IFACE_PLAYER}.{method}",
            ],
            timeout=2.0,
        )

    def set_position(self, position: int, track_id: str) -> None:
        """
        Seek to an absolute position.

        MPRIS signature: ``SetPosition(o trackId, x position)``
        * trackId must match the current track's ``mpris:trackid``
        * position is in **microseconds**

        Strawberry uses object-path track ids; we pass them as ``objpath:``.
        """
        bus = self.ensure_bus()
        if not bus or not self.player or not track_id:
            raise RuntimeError("no player/track")
        run_dbus_send(
            bus,
            [
                f"--dest={self.player}",
                MPRIS_PATH,
                f"{IFACE_PLAYER}.SetPosition",
                f"objpath:{track_id}",
                f"int64:{int(position)}",
            ],
            timeout=2.0,
        )

    def set_volume(self, volume: float) -> None:
        """
        Set player volume (0.0 – 1.0) via Properties.Set on ``Volume``.

        Not all players support this; callers should check canControlVolume.
        """
        bus = self.ensure_bus()
        if not bus or not self.player:
            raise RuntimeError("no player")
        volume = max(0.0, min(1.0, float(volume)))
        run_dbus_send(
            bus,
            [
                f"--dest={self.player}",
                MPRIS_PATH,
                "org.freedesktop.DBus.Properties.Set",
                f"string:{IFACE_PLAYER}",
                "string:Volume",
                f"variant:double:{volume}",
            ],
            timeout=2.0,
        )

    # ------------------------------------------------------------------
    # Album art
    # ------------------------------------------------------------------

    def cache_album_art(
        self, art_url: str, cache_dir: str, previous: str
    ) -> Tuple[str, str]:
        """
        Make local (``file://``) cover art visible inside the Steam UI.

        Steam's CEF UI cannot read arbitrary filesystem paths. The original
        MusicControl trick:

        1. Copy the cover into the plugin runtime cache directory.
        2. Symlink that cache into
           ``~/.local/share/Steam/steamui/images/deckycache_musicControl/``
           (created once in Plugin._main).
        3. Point the <img> at
           ``https://steamloopback.host/images/deckycache_musicControl/<file>``

        Remote ``https://`` art URLs are returned unchanged (Steam can load them).

        Returns
        -------
        (display_url, new_previous_path)
            display_url is what the <img src> should use.
            new_previous_path is the on-disk cache file to delete later
            when the track changes (or the old previous if we reused a file).
        """
        if not art_url:
            return "", previous

        # HTTP(S) art — no local copy needed
        if not art_url.startswith("file:"):
            return art_url, previous

        # file:///path/to/cover.jpg → /path/to/cover.jpg
        path = unquote(urlparse(art_url).path)
        if not path or not os.path.exists(path):
            return "", previous

        base = os.path.basename(path) or "cover.jpg"
        stem, ext = os.path.splitext(base)
        # Include a hash of the full path so two albums with "cover.jpg"
        # don't clobber each other in the cache directory
        safe = f"{stem}_{abs(hash(path)) & 0xFFFFFFFF:x}{ext or '.jpg'}"
        target = os.path.join(cache_dir, safe)

        if os.path.isfile(target):
            # Already copied this exact cover earlier in the session
            return (
                f"https://steamloopback.host/images/deckycache_musicControl/{safe}",
                previous,
            )

        # Free the previous track's cover to avoid unbounded cache growth
        if previous and os.path.exists(previous) and previous != target:
            try:
                os.remove(previous)
            except Exception:
                pass

        shutil.copy2(path, target)
        return (
            f"https://steamloopback.host/images/deckycache_musicControl/{safe}",
            target,
        )
