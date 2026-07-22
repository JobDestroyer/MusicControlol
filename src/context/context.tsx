import { createContext, useContext, useReducer, type ReactNode } from "react";
import type { PlayerInfo, PlayerStatus, TrackMetadata } from "../types";
import { defaultState, type AppState } from "./defaultState";

export enum AppActions {
  SetDefaultState,
  SetIsSeeking,
  SeekToPosition,
  SetIsAdjustingVolume,
  AdjustVolumeByUser,
  SetPlayingStateByUser,
  SetHasChangedPlaybackState,
  SetActiveProvider,
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

function applyMetadata(meta: TrackMetadata): Partial<AppState> {
  return {
    currentSong: meta.title || defaultState.currentSong,
    currentArtist: meta.artist || defaultState.currentArtist,
    currentArtUrl: meta.artUrl || defaultState.currentArtUrl,
    hasAvailableTrack: Boolean(meta.title || meta.trackid || meta.artUrl),
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
        // keep seek/volume interaction flags cleared
        isSeeking: false,
        isSettingVolume: false,
        emptyHint: true,
      };
    case AppActions.SetIsSeeking:
      return { ...state, isSeeking: action.value };
    case AppActions.SetHasChangedPlaybackState:
      return { ...state, hasChangedPlaybackState: action.value };
    case AppActions.SeekToPosition:
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

      if (!state.hasChangedPlaybackState) {
        next.currentTrackStatus = status.playbackStatus || state.currentTrackStatus;
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

export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(mainReducer, defaultState);
  return (
    <AppStateContext.Provider value={{ state, dispatch }}>
      {children}
    </AppStateContext.Provider>
  );
};

export function useStateContext() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error("useStateContext must be used within AppContextProvider");
  }
  return context;
}

export { defaultState, AppStateContext };
