"""Persistent plugin settings under DECKY_PLUGIN_SETTINGS_DIR."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import decky  # type: ignore

_SETTINGS_FILE = "settings.json"
_DEFAULTS: Dict[str, Any] = {
    "preferredPlayer": "",
}


def _path() -> str:
    base = decky.DECKY_PLUGIN_SETTINGS_DIR or ""
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".config", "music-control")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, _SETTINGS_FILE)


def load_settings() -> Dict[str, Any]:
    path = _path()
    data = dict(_DEFAULTS)
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:
        pass
    return data


def save_settings(data: Dict[str, Any]) -> None:
    path = _path()
    merged = dict(_DEFAULTS)
    merged.update(data)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
    except Exception:
        pass


def get_preferred_player() -> str:
    return str(load_settings().get("preferredPlayer") or "")


def set_preferred_player(player: str) -> None:
    data = load_settings()
    data["preferredPlayer"] = player or ""
    save_settings(data)
