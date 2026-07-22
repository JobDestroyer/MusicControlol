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
