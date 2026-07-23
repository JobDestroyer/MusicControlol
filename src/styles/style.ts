/**
 * style.ts
 * --------
 * Shared inline CSSProperties for the MusicControl panel.
 * Kept as plain objects (not CSS modules) so they work inside Steam's
 * CEF environment without extra loaders.
 */

import type { CSSProperties } from "react";

/** Horizontal rule under the transport buttons. */
export const musicControlDividerStyle: CSSProperties = {
  content: "",
  bottom: "-0.5px",
  left: "0",
  right: "0",
  height: "1px",
  background: "#23262e",
  // Bleed past the panel padding so the line spans the full QAM width
  width: "calc(100% + 32px)",
  marginLeft: "-16px",
  marginRight: "-16px",
};

/** First (leftmost) transport button — no left margin. */
export const musicControlButtonStyleFirst: CSSProperties = {
  marginLeft: "0px",
  height: "30px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "5px 0px 0px 0px",
  minWidth: "0",
};

/** Subsequent transport buttons — small gap from the previous one. */
export const musicControlButtonStyle: CSSProperties = {
  marginLeft: "5px",
  height: "30px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "5px 0px 0px 0px",
  minWidth: "0",
};

/**
 * Title / artist text: fixed max width with ellipsis so long track names
 * don't push the album art or wrap awkwardly in the narrow QAM column.
 */
export const musicControlFieldStyle: CSSProperties = {
  width: "180px",
  overflow: "hidden",
  whiteSpace: "nowrap",
  textOverflow: "ellipsis",
};
