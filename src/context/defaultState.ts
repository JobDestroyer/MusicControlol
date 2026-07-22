import default_music from "../../assets/default_music.png";
import type { PlayerInfo } from "../types";

export const defaultState = {
  hasChangedPlaybackState: false,
  isSeeking: false,
  isSettingVolume: false,
  hasAvailableTrack: false,
  currentSong: "Not Playing",
  currentArtist: "Unknown Artist",
  currentArtUrl: default_music as string,
  currentTrackId: "",
  currentTrackProgress: 0,
  currentTrackLength: 1,
  currentTrackStatus: "Paused",
  currentServiceProvider: "",
  currentIdentity: "",
  providers: [] as string[],
  providersToIdentity: [] as PlayerInfo[],
  currentVolume: 1.0,
  canModifyVolume: false,
  canSeek: false,
  emptyHint: false,
};

export type AppState = typeof defaultState;
