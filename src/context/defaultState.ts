/**
 * defaultState.ts
 * ---------------
 * Initial / empty UI state for the MusicControl panel.
 *
 * `default_music.png` is the placeholder cover shown when nothing is playing
 * or art is unavailable. Rollup rewrites the import to a steamloopback URL.
 */

import default_music from "../../assets/default_music.png";
import type { PlayerInfo } from "../types";

/**
 * Full React state shape for the panel.
 *
 * Interaction flags (isSeeking, isSettingVolume, hasChangedPlaybackState)
 * prevent the 1 Hz poll from overwriting the user's in-progress drag or
 * optimistic play/pause toggle until a short timeout expires.
 */
export const defaultState = {
  /** True for ~1s after the user hits play/pause, so poll won't flip the icon back */
  hasChangedPlaybackState: false,

  /** True while the user is dragging the seek slider */
  isSeeking: false,

  /** True while the user is dragging the volume slider */
  isSettingVolume: false,

  /** True when metadata looks like a real track */
  hasAvailableTrack: false,

  currentSong: "Not Playing",
  currentArtist: "Unknown Artist",

  /** Cover art URL (steamloopback, https, or placeholder asset) */
  currentArtUrl: default_music as string,

  /** mpris:trackid — required for seek */
  currentTrackId: "",

  /** Position and length are stored in *microseconds* (MPRIS units) */
  currentTrackProgress: 0,
  currentTrackLength: 1,

  /** "Playing" | "Paused" | "Stopped" */
  currentTrackStatus: "Paused",

  /** Selected org.mpris.MediaPlayer2.* bus name */
  currentServiceProvider: "",

  /** Friendly Identity for the selected player */
  currentIdentity: "",

  /** Bus names for the provider menu */
  providers: [] as string[],

  /** Full player rows for identity lookup in the menu */
  providersToIdentity: [] as PlayerInfo[],

  /** 0.0 – 1.0 */
  currentVolume: 1.0,
  canModifyVolume: false,
  canSeek: false,

  /**
   * True when the last poll found no MPRIS players — drives the empty-state
   * copy ("Start a media player from Game Mode").
   */
  emptyHint: false,
};

export type AppState = typeof defaultState;
