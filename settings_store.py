"""
settings_store.py
=================

Purpose
-------
Persist small amounts of user preference across plugin reloads / Deck reboots.

Currently stored
----------------
* ``preferredPlayer`` — last MPRIS bus name the user explicitly selected
  in the provider menu (e.g. ``org.mpris.MediaPlayer2.strawberry``).

  On the next ``poll()``, if that name is still online, we select it
  instead of always defaulting to whatever ListNames returned first.

Where files live
----------------
Decky documents ``DECKY_PLUGIN_SETTINGS_DIR`` as the correct place for
plugin settings. On a Deck that is typically::

    ~/homebrew/settings/<plugin-folder-name>/

We write a single JSON file there: ``settings.json``.

If Decky ever fails to set the env var (e.g. unit tests, odd installs),
we fall back to ``~/.config/music-control/`` so the code still works.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import decky  # type: ignore  # injected by Decky Loader at runtime

# Filename inside the settings directory
_SETTINGS_FILE = "settings.json"

# Defaults applied when the file is missing or incomplete
_DEFAULTS: Dict[str, Any] = {
    # Empty string means "no preference — pick the first available player"
    "preferredPlayer": "",
}


def _path() -> str:
    """
    Absolute path to settings.json, creating the parent directory if needed.
    """
    base = decky.DECKY_PLUGIN_SETTINGS_DIR or ""
    if not base:
        # Dev / fallback path when Decky constants are unavailable
        base = os.path.join(os.path.expanduser("~"), ".config", "music-control")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, _SETTINGS_FILE)


def load_settings() -> Dict[str, Any]:
    """
    Read settings from disk, merged over defaults.

    Never raises: a corrupt file simply yields defaults.
    """
    path = _path()
    data = dict(_DEFAULTS)
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:
        # JSON error, permission error, etc. — keep defaults
        pass
    return data


def save_settings(data: Dict[str, Any]) -> None:
    """
    Write settings to disk (defaults + provided keys).

    Never raises: a write failure is silently ignored so the plugin
    keeps working even on a read-only filesystem.
    """
    path = _path()
    merged = dict(_DEFAULTS)
    merged.update(data)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
    except Exception:
        pass


def get_preferred_player() -> str:
    """Return the saved preferred MPRIS bus name, or ``\"\"``."""
    return str(load_settings().get("preferredPlayer") or "")


def set_preferred_player(player: str) -> None:
    """
    Remember the user's player choice.

    Called from ``Plugin.set_player`` when the UI provider menu is used.
    """
    data = load_settings()
    data["preferredPlayer"] = player or ""
    save_settings(data)
