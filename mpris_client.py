"""Cached MPRIS client using dbus-send."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse
import shutil

from bus_discover import (
    MPRIS_PREFIX,
    discover_players,
    run_dbus_send,
)
from mpris_parse import (
    identity_from_bus_name,
    parse_metadata,
    parse_player_get_all,
    parse_variant_string,
)

MPRIS_PATH = "/org/mpris/MediaPlayer2"
IFACE_ROOT = "org.mpris.MediaPlayer2"
IFACE_PLAYER = "org.mpris.MediaPlayer2.Player"

# How long to reuse ListNames / identities without rediscovery
PLAYERS_TTL_SEC = 3.0
# How long to trust a bus address before full rediscovery on failure
BUS_STICKY_SEC = 60.0


class MprisClient:
    def __init__(self) -> None:
        self.bus_address: str = ""
        self.player: str = ""
        self._players_cache: List[Dict[str, str]] = []
        self._players_cache_at: float = 0.0
        self._bus_ok_at: float = 0.0
        self._identity_cache: Dict[str, str] = {}

    def _set_bus(self, addr: str) -> None:
        if not addr:
            return
        self.bus_address = addr
        self._bus_ok_at = time.monotonic()
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = addr

    def ensure_bus(self, force: bool = False) -> str:
        now = time.monotonic()
        if (
            not force
            and self.bus_address
            and now - self._bus_ok_at < BUS_STICKY_SEC
        ):
            return self.bus_address
        names, addr = discover_players()
        if addr:
            self._set_bus(addr)
            # seed player list cache if we just listed
            if names:
                self._players_cache = self._names_to_players(names, addr)
                self._players_cache_at = now
        return self.bus_address

    def _names_to_players(self, names: List[str], bus: str) -> List[Dict[str, str]]:
        players: List[Dict[str, str]] = []
        for name in names:
            identity = self._identity_cache.get(name)
            if not identity:
                identity = identity_from_bus_name(name)
                try:
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
                    pass
                self._identity_cache[name] = identity
            players.append({"busName": name, "identity": identity})
        return players

    def list_players(self, force: bool = False) -> List[Dict[str, str]]:
        now = time.monotonic()
        if (
            not force
            and self._players_cache
            and now - self._players_cache_at < PLAYERS_TTL_SEC
        ):
            return list(self._players_cache)

        bus = self.ensure_bus(force=force)
        if not bus:
            # try full discover even if sticky empty
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

        try:
            from bus_discover import list_mpris_names

            names = list_mpris_names(bus)
        except Exception:
            # bus may have died — rediscover once
            names, addr = discover_players()
            if not addr:
                self._players_cache = []
                self._players_cache_at = now
                return []
            self._set_bus(addr)
            bus = addr
            names = names

        players = self._names_to_players(names, bus)
        self._players_cache = players
        self._players_cache_at = now
        # drop identity cache for vanished players
        live = {p["busName"] for p in players}
        self._identity_cache = {
            k: v for k, v in self._identity_cache.items() if k in live
        }
        return list(players)

    def pick_player(self, preferred: str, players: List[Dict[str, str]]) -> str:
        names = [p["busName"] for p in players]
        if not names:
            return ""
        if preferred and preferred in names:
            return preferred
        if self.player and self.player in names:
            return self.player
        return names[0]

    def get_status(self, dest: Optional[str] = None) -> Dict[str, Any]:
        empty: Dict[str, Any] = {
            "available": False,
            "hasTrack": False,
            "player": dest or self.player,
            "identity": "",
            "playbackStatus": "Stopped",
            "position": 0,
            "volume": 0.0,
            "canSeek": False,
            "canControlVolume": False,
            "metadata": {},
            "error": "",
        }
        bus = self.ensure_bus()
        player = dest or self.player
        if not bus or not player:
            return empty

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
            # Fallback: individual Gets
            try:
                parsed = self._status_via_individual_gets(bus, player)
            except Exception as e:
                empty["error"] = str(e)
                return empty

        meta = parsed.get("metadata") or {}
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

        from mpris_parse import parse_variant_bool, parse_variant_number

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

    def call(self, method: str) -> None:
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

    def cache_album_art(
        self, art_url: str, cache_dir: str, previous: str
    ) -> Tuple[str, str]:
        """
        Returns (display_url, new_previous_path).
        """
        if not art_url:
            return "", previous
        if not art_url.startswith("file:"):
            return art_url, previous
        path = unquote(urlparse(art_url).path)
        if not path or not os.path.exists(path):
            return "", previous

        base = os.path.basename(path) or "cover.jpg"
        stem, ext = os.path.splitext(base)
        safe = f"{stem}_{abs(hash(path)) & 0xFFFFFFFF:x}{ext or '.jpg'}"
        target = os.path.join(cache_dir, safe)

        if os.path.isfile(target):
            # already cached this file
            return (
                f"https://steamloopback.host/images/deckycache_musicControl/{safe}",
                previous,
            )

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
