"""
mpris_util.py
=============

Purpose
-------
Helpers for normalizing **typed** MPRIS Metadata maps into plain JSON-friendly
dicts. Used primarily by unit tests, and kept available if we ever switch the
runtime backend from text-scraping ``dbus-send`` to a real D-Bus library
(jeepney / dbus-next), which returns Python tuples/lists instead of text.

Why "unwrap_variant"?
---------------------
In the D-Bus type system, property values are often wrapped as *variants*.
Python D-Bus bindings commonly surface a variant as a 2-tuple::

    (signature: str, value: Any)

Example::

    ("s", "Hello")           # string
    ("x", 123456789)         # int64
    ("as", ["A", "B"])       # array of strings
    ("o", "/path/to/track")  # object path

``unwrap_variant`` recursively strips those wrappers so callers see bare
Python values.
"""

from __future__ import annotations

from typing import Any, Dict


def unwrap_variant(value: Any) -> Any:
    """
    Recursively unwrap D-Bus variant tuples, lists, and dicts.

    A value is treated as a variant only when it looks like
    ``(short_signature, payload)`` where the signature is a short D-Bus type
    string (e.g. ``s``, ``x``, ``as``, ``a{sv}``). This avoids mis-detecting
    arbitrary 2-tuples that happen to start with a long string.
    """
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        sig = value[0]
        # Real D-Bus signatures are short; refuse long strings
        if len(sig) <= 16 and all(c.isalnum() or c in "{}()[]" for c in sig):
            return unwrap_variant(value[1])
    if isinstance(value, list):
        return [unwrap_variant(v) for v in value]
    if isinstance(value, dict):
        return {k: unwrap_variant(v) for k, v in value.items()}
    return value


def metadata_to_dict(raw: Any) -> Dict[str, Any]:
    """
    Convert an MPRIS Metadata map into the flat shape the frontend uses.

    Input keys use MPRIS namespaces (``mpris:``, ``xesam:``).
    Output keys are plain: ``title``, ``artist``, ``artUrl``, ``length``,
    ``trackid``, ``album``, ``url``.

    ``xesam:artist`` may be a list (multi-artist tracks); we join with commas.
    """
    data = unwrap_variant(raw)
    if not isinstance(data, dict):
        return {}

    out: Dict[str, Any] = {}

    trackid = data.get("mpris:trackid")
    if trackid is not None:
        out["trackid"] = str(trackid)

    length = data.get("mpris:length")
    if length is not None:
        try:
            out["length"] = int(length)
        except (TypeError, ValueError):
            pass

    art = data.get("mpris:artUrl")
    if art:
        out["artUrl"] = str(art)

    title = data.get("xesam:title")
    if title is not None:
        out["title"] = str(title)

    album = data.get("xesam:album")
    if album is not None:
        out["album"] = str(album)

    artists = data.get("xesam:artist")
    if artists is not None:
        if isinstance(artists, (list, tuple)):
            out["artist"] = ", ".join(str(a) for a in artists if a)
        else:
            out["artist"] = str(artists)

    url = data.get("xesam:url")
    if url is not None:
        out["url"] = str(url)

    return out
