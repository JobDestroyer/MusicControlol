/**
 * context.tsx
 * -----------
 * React state container for the MusicControl panel.
 *
 * Pattern: classic useReducer + Context.
 *   * Components call `useStateContext()` to read `state` and `dispatch`.
 *   * The main poll loop dispatches a single `SetSnapshot` per tick.
 *   * Transport buttons / sliders dispatch small interaction actions
 *     (seek, volume, optimistic play/pause) that temporarily suppress
 *     poll overwrites.
 */

import { createContext, useContext, useReducer, type ReactNode } from "react";
import type { PlayerInfo, PlayerStatus, TrackMetadata } from "../types";
import { defaultState, type AppState } from "./defaultState";

/** Discriminated action types the reducer understands. */
export enum AppActions {
  /** Reset to empty / "not playing" defaults (no players online). */
  SetDefaultState,

  /** Clear or set the "user is seeking" flag. */
  SetIsSeeking,

  /** User moved the seek slider — update position and set isSeeking. */
  SeekToPosition,

  /** Clear or set the "user is adjusting volume" flag. */
  SetIsAdjustingVolume,

  /** User moved the volume slider. */
  AdjustVolumeByUser,

  /** Optimistic play/pause icon flip after a button press. */
  SetPlayingStateByUser,

  /** Clear the optimistic play/pause lock after a short delay. */
  SetHasChangedPlaybackState,

  /** User picked a provider from the menu (optimistic selection). */
  SetActiveProvider,

  /**
   * Full frame from Python `poll()` — players list + status.
   * This is the hot path (~1 Hz while the panel is open).
   */
  SetSnapshot,
}

type Action =
  | { type: AppActions.SetDefaultState }
  | { type: AppActions.SetIsSeeking; value: boolean }
  | { type: AppActions.SeekToPosition; value: number }
  | { type: AppActions.SetIsAdjustingVolume; value: boolean }
  | { type: AppActions.AdjustVolumeByUser; value: number }
  | { type: AppActions.SetPlayingStateByUser; value: string }
  | { type: AppActions.SetHasChangedPlaybackState; value: boolean }
  | { type: AppActions.SetActiveProvider; value: string }
  | {
      type: AppActions.SetSnapshot;
      players: PlayerInfo[];
      status: PlayerStatus;
    };

type Dispatch = (action: Action) => void;

const AppStateContext = createContext<{
  state: AppState;
  dispatch: Dispatch;
}>({
  state: defaultState,
  dispatch: () => null,
});

/**
 * Map backend metadata fields onto the UI state slice for the current track.
 * Missing fields fall back to the default "Not Playing" placeholders.
 */
function applyMetadata(meta: TrackMetadata): Partial<AppState> {
  return {
    currentSong: meta.title || defaultState.currentSong,
    currentArtist: meta.artist || defaultState.currentArtist,
    currentArtUrl: meta.artUrl || defaultState.currentArtUrl,
    hasAvailableTrack: Boolean(meta.title || meta.trackid || meta.artUrl),
    // length is microseconds; keep a minimum of 1 so the seek slider math
    // never divides by zero
    currentTrackLength:
      meta.length && meta.length > 0 ? meta.length : defaultState.currentTrackLength,
    currentTrackId: meta.trackid || "",
  };
}

function mainReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case AppActions.SetDefaultState:
      return {
        ...defaultState,
        isSeeking: false,
        isSettingVolume: false,
        emptyHint: true,
      };

    case AppActions.SetIsSeeking:
      return { ...state, isSeeking: action.value };

    case AppActions.SetHasChangedPlaybackState:
      return { ...state, hasChangedPlaybackState: action.value };

    case AppActions.SeekToPosition:
      // Freeze poll-driven position updates until isSeeking is cleared
      return { ...state, currentTrackProgress: action.value, isSeeking: true };

    case AppActions.SetPlayingStateByUser:
      return {
        ...state,
        currentTrackStatus: action.value,
        hasChangedPlaybackState: true,
      };

    case AppActions.SetIsAdjustingVolume:
      return { ...state, isSettingVolume: action.value };

    case AppActions.AdjustVolumeByUser:
      return { ...state, currentVolume: action.value, isSettingVolume: true };

    case AppActions.SetActiveProvider:
      return { ...state, currentServiceProvider: action.value };

    case AppActions.SetSnapshot: {
      const { players, status } = action;
      const busNames = players.map((p) => p.busName);

      // Nothing online (or backend said available=false)
      if (!players.length || !status.available) {
        return {
          ...defaultState,
          emptyHint: true,
          providers: busNames,
          providersToIdentity: players,
        };
      }

      const meta = status.metadata || {};
      const next: AppState = {
        ...state,
        emptyHint: false,
        providers: busNames,
        providersToIdentity: players,
        currentServiceProvider: status.player || state.currentServiceProvider,
        currentIdentity: status.identity || "",
        canSeek: status.canSeek,
        canModifyVolume: status.canControlVolume,
        ...applyMetadata(meta),
      };

      // Respect in-flight user interactions — don't yank the icon/slider
      if (!state.hasChangedPlaybackState) {
        next.currentTrackStatus =
          status.playbackStatus || state.currentTrackStatus;
      }
      if (!state.isSeeking) {
        next.currentTrackProgress = status.position || 0;
      }
      if (!state.isSettingVolume && status.canControlVolume) {
        next.currentVolume = status.volume;
      }

      return next;
    }

    default:
      return state;
  }
}

/** Provider that wraps the plugin panel content. */
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(mainReducer, defaultState);
  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  );
};

/** Hook for child components — throws if used outside the provider. */
export function useStateContext() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error("useStateContext must be used within AppContextProvider");
  }
  return context;
}

export { defaultState, AppStateContext };
