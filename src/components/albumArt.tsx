/**
 * albumArt.tsx
 * ------------
 * 80×80 cover image for the current track.
 *
 * Local players (Strawberry) usually expose `file:///...` art paths.
 * Steam's CEF cannot read those directly, so we ask Python
 * `cache_album_art` to copy the file into a Steam-visible cache and
 * return a `https://steamloopback.host/images/...` URL.
 *
 * Remote `https://` art (Spotify) is used as-is.
 */

import { useEffect, useState, type FC } from "react";
import { cacheAlbumArt } from "../backend";
import { defaultState } from "../context/defaultState";

export const AlbumArt: FC<{ albumArt: string }> = ({ albumArt }) => {
  // What we actually put in <img src> (may lag albumArt while caching)
  const [displayUrl, setDisplayUrl] = useState<string>(defaultState.currentArtUrl);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      // Nothing / placeholder — show default art
      if (!albumArt || albumArt === defaultState.currentArtUrl) {
        if (!cancelled) setDisplayUrl(defaultState.currentArtUrl);
        return;
      }

      // Local file — must go through the backend cache
      if (albumArt.startsWith("file:") || albumArt.startsWith("file:///")) {
        try {
          const cached = await cacheAlbumArt(albumArt);
          if (!cancelled) {
            setDisplayUrl(cached || defaultState.currentArtUrl);
          }
        } catch {
          if (!cancelled) setDisplayUrl(defaultState.currentArtUrl);
        }
        return;
      }

      // Already a loadable URL (http/https/steamloopback)
      if (!cancelled) setDisplayUrl(albumArt);
    })();

    return () => {
      // Ignore late results if albumArt changed mid-flight
      cancelled = true;
    };
  }, [albumArt]);

  return (
    <div style={{ width: "80px", height: "80px", flexShrink: 0 }}>
      <img
        style={{
          borderRadius: "5px",
          width: "80px",
          height: "80px",
          objectFit: "cover",
        }}
        src={displayUrl}
        alt=""
        onError={({ currentTarget }) => {
          // Broken image URL → fall back to placeholder once
          if (currentTarget.src === defaultState.currentArtUrl) return;
          currentTarget.src = defaultState.currentArtUrl;
        }}
      />
    </div>
  );
};
