import { callable } from "@decky/api";
import type { PlayerInfo, PlayerStatus, PollSnapshot } from "./types";

export const poll = callable<[], PollSnapshot>("poll");
export const listPlayers = callable<[], PlayerInfo[]>("list_players");
export const setPlayer = callable<[player: string], string>("set_player");
export const getPlayer = callable<[], string>("get_player");
export const getStatus = callable<[], PlayerStatus>("get_status");
export const playPause = callable<[], boolean>("play_pause");
export const nextTrack = callable<[], boolean>("next_track");
export const previousTrack = callable<[], boolean>("previous_track");
export const setPosition = callable<
  [position: number, trackId: string],
  boolean
>("set_position");
export const setVolume = callable<[volume: number], boolean>("set_volume");
export const cacheAlbumArt = callable<[artUrl: string], string>(
  "cache_album_art"
);
