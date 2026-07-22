"""Pure helpers for MPRIS variant/metadata normalization (no decky / D-Bus I/O)."""

from __future__ import annotations

from typing import Any, Dict


def unwrap_variant(value: Any) -> Any:
    """Jeepney returns D-Bus variants as (signature, value) tuples."""
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        # Avoid treating (trackid_string_that_looks_like_sig, something) wrongly:
        # real signatures are short (e.g. s, x, as, o, a{sv})
        sig = value[0]
        if len(sig) <= 16 and all(c.isalnum() or c in "{}()[]" for c in sig):
            return unwrap_variant(value[1])
    if isinstance(value, list):
        return [unwrap_variant(v) for v in value]
    if isinstance(value, dict):
        return {k: unwrap_variant(v) for k, v in value.items()}
    return value


def metadata_to_dict(raw: Any) -> Dict[str, Any]:
    """Normalize MPRIS Metadata map to a JSON-friendly dict for the frontend."""
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
