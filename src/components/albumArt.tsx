import { useEffect, useState, type FC } from "react";
import { cacheAlbumArt } from "../backend";
import { defaultState } from "../context/defaultState";

export const AlbumArt: FC<{ albumArt: string }> = ({ albumArt }) => {
  const [displayUrl, setDisplayUrl] = useState<string>(defaultState.currentArtUrl);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (!albumArt || albumArt === defaultState.currentArtUrl) {
        if (!cancelled) setDisplayUrl(defaultState.currentArtUrl);
        return;
      }

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

      if (!cancelled) setDisplayUrl(albumArt);
    })();

    return () => {
      cancelled = true;
    };
  }, [albumArt]);

  return (
    <div style={{ width: "80px", height: "80px", flexShrink: 0 }}>
      <img
        style={{ borderRadius: "5px", width: "80px", height: "80px", objectFit: "cover" }}
        src={displayUrl}
        alt=""
        onError={({ currentTarget }) => {
          if (currentTarget.src === defaultState.currentArtUrl) return;
          currentTarget.src = defaultState.currentArtUrl;
        }}
      />
    </div>
  );
};
