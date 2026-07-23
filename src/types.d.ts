/**
 * types.d.ts
 * ----------
 * Shared TypeScript types for the MusicControl frontend.
 *
 * Also declares ambient modules so TypeScript accepts asset imports
 * like `import img from "../assets/foo.png"` (rollup-plugin / @decky/rollup
 * turns those into URLs at build time).
 */

declare module "*.svg" {
  const content: string;
  export default content;
}

declare module "*.png" {
  const content: string;
  export default content;
}

declare module "*.jpg" {
  const content: string;
  export default content;
}

/** One row in the media-provider picker menu. */
export type PlayerInfo = {
  /** D-Bus well-known name, e.g. "org.mpris.MediaPlayer2.strawberry" */
  busName: string;
  /** Friendly label from MPRIS Identity, e.g. "Strawberry" */
  identity: string;
};

/**
 * Flat track metadata after Python-side parsing.
 * Field names match what mpris_parse / mpris_util emit (no mpris:/xesam: prefixes).
 */
export type TrackMetadata = {
  title?: string;
  artist?: string;
  album?: string;
  /** file:// or https:// cover art */
  artUrl?: string;
  /** Track length in microseconds (MPRIS standard) */
  length?: number;
  /** Object path or string id used by SetPosition */
  trackid?: string;
  url?: string;
};

/** Status of the currently selected player (or empty defaults if none). */
export type PlayerStatus = {
  /** True if we successfully talked to a player on the bus */
  available: boolean;
  /** True if metadata looks like a real track (title/trackid/art) */
  hasTrack?: boolean;
  /** Selected bus name */
  player: string;
  /** Friendly Identity string */
  identity: string;
  /** "Playing" | "Paused" | "Stopped" */
  playbackStatus: string;
  /** Position in microseconds */
  position: number;
  /** 0.0 – 1.0 */
  volume: number;
  canSeek: boolean;
  canControlVolume: boolean;
  metadata: TrackMetadata;
  /** Non-empty only when the backend hit an error */
  error: string;
};

/**
 * Single payload from Python `poll()` — everything the UI needs for one frame.
 */
export type PollSnapshot = {
  players: PlayerInfo[];
  status: PlayerStatus;
};
