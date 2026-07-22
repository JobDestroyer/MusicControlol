import { callable } from "@decky/api";
import type { PlayerInfo, PlayerStatus } from "./types";

export type DebugInfo = {
  uid: number;
  deckyUser: string;
  busAddress: string;
  candidates: string[];
  players: string[];
  note: string;
  error: string;
  dbusSend: string;
  version?: string;
  jeepney?: boolean;
};

export type PingInfo = {
  ok: boolean;
  version: string;
  uid: number;
  deckUid: number;
  bus: string;
  jeepney: boolean;
  dbusSend: boolean;
  note: string;
  player: string;
};

const listPlayersRaw = callable<[], PlayerInfo[]>("list_players");
const setPlayerRaw = callable<[player: string], string>("set_player");
const getPlayerRaw = callable<[], string>("get_player");
const getStatusRaw = callable<[], PlayerStatus>("get_status");
const playPauseRaw = callable<[], boolean>("play_pause");
const nextTrackRaw = callable<[], boolean>("next_track");
const previousTrackRaw = callable<[], boolean>("previous_track");
const setPositionRaw = callable<
  [position: number, trackId: string],
  boolean
>("set_position");
const setVolumeRaw = callable<[volume: number], boolean>("set_volume");
const cacheAlbumArtRaw = callable<[artUrl: string], string>("cache_album_art");
const debugInfoRaw = callable<[], DebugInfo>("debug_info");
const pingRaw = callable<[], PingInfo>("ping");

function withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const t = window.setTimeout(() => {
      reject(new Error(`${label} timed out after ${ms}ms (backend hung or not loaded)`));
    }, ms);
    p.then(
      (v) => {
        window.clearTimeout(t);
        resolve(v);
      },
      (e) => {
        window.clearTimeout(t);
        reject(e);
      }
    );
  });
}

export const ping = () => withTimeout(pingRaw(), 3000, "ping");
export const listPlayers = () => withTimeout(listPlayersRaw(), 8000, "list_players");
export const setPlayer = (player: string) =>
  withTimeout(setPlayerRaw(player), 3000, "set_player");
export const getPlayer = () => withTimeout(getPlayerRaw(), 3000, "get_player");
export const getStatus = () => withTimeout(getStatusRaw(), 8000, "get_status");
export const playPause = () => withTimeout(playPauseRaw(), 3000, "play_pause");
export const nextTrack = () => withTimeout(nextTrackRaw(), 3000, "next_track");
export const previousTrack = () =>
  withTimeout(previousTrackRaw(), 3000, "previous_track");
export const setPosition = (position: number, trackId: string) =>
  withTimeout(setPositionRaw(position, trackId), 3000, "set_position");
export const setVolume = (volume: number) =>
  withTimeout(setVolumeRaw(volume), 3000, "set_volume");
export const cacheAlbumArt = (artUrl: string) =>
  withTimeout(cacheAlbumArtRaw(artUrl), 5000, "cache_album_art");
export const debugInfo = () => withTimeout(debugInfoRaw(), 8000, "debug_info");
