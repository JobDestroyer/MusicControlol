/**
 * backend.ts
 * ----------
 * Thin TypeScript wrappers around the Python methods defined on
 * `Plugin` in main.py.
 *
 * How Decky RPC works (api_version 1):
 *   1. `@decky/api` connects to the loader using the plugin name from
 *      plugin.json ("MusicControl").
 *   2. `callable<[Args], Return>("method_name")` returns a function that,
 *      when called, asks the loader to run `Plugin.method_name(*args)` in
 *      the plugin's Python process and returns a Promise of the result.
 *
 * Method names must match the Python `async def` names exactly
 * (e.g. "play_pause", not "playPause").
 */

import { callable } from "@decky/api";
import type { PlayerInfo, PlayerStatus, PollSnapshot } from "./types";

/**
 * Primary tick API: one round-trip for player list + current track status.
 * Prefer this over calling listPlayers + getStatus separately.
 */
export const poll = callable<[], PollSnapshot>("poll");

/** List active MPRIS players as { busName, identity }[]. */
export const listPlayers = callable<[], PlayerInfo[]>("list_players");

/**
 * Select which player subsequent controls affect.
 * Also persists the choice on the Python side (settings_store).
 */
export const setPlayer = callable<[player: string], string>("set_player");

/** Currently selected bus name (may be empty string). */
export const getPlayer = callable<[], string>("get_player");

/** Status for the currently selected player only. */
export const getStatus = callable<[], PlayerStatus>("get_status");

/** Toggle play/pause. */
export const playPause = callable<[], boolean>("play_pause");

/** Skip forward one track. */
export const nextTrack = callable<[], boolean>("next_track");

/** Skip backward one track. */
export const previousTrack = callable<[], boolean>("previous_track");

/**
 * Seek to an absolute position.
 * @param position - Microseconds into the track (MPRIS unit).
 * @param trackId  - Must match the current mpris:trackid object path/string.
 */
export const setPosition = callable<
  [position: number, trackId: string],
  boolean
>("set_position");

/**
 * Set playback volume.
 * @param volume - 0.0 … 1.0
 */
export const setVolume = callable<[volume: number], boolean>("set_volume");

/**
 * Prepare cover art for Steam UI display.
 * Local file:// URLs are copied into a Steam-visible cache; https URLs pass through.
 */
export const cacheAlbumArt = callable<[artUrl: string], string>(
  "cache_album_art"
);
