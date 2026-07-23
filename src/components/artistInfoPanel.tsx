/**
 * artistInfoPanel.tsx
 * -------------------
 * Two-line text block next to the album art: track title + artist.
 * Ellipsis styles come from musicControlFieldStyle so long names don't
 * blow out the QAM panel width.
 */

import type { FC } from "react";
import { musicControlFieldStyle } from "../styles/style";

export const ArtistInfoPanel: FC<{ title: string; artist: string }> = ({
  title,
  artist,
}) => {
  return (
    <div style={{ marginLeft: "10px", minWidth: 0 }}>
      <div style={{ ...musicControlFieldStyle, fontWeight: 600 }}>{title}</div>
      <div style={{ ...musicControlFieldStyle, opacity: 0.8, fontSize: "0.9em" }}>
        {artist}
      </div>
    </div>
  );
};
