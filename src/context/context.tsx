import { createContext, useContext, useReducer, type ReactNode } from "react";
import type { PlayerInfo, TrackMetadata } from "../types";
import { defaultMeta, defaultState, type AppState } from "./defaultState";

export enum AppActions {
  SetDefaultState,
  SetDefaultMeta,
  SetIsSeeking,
  SeekToPosition,
  SetIsAdjustingVolume,
  AdjustVolumeByUser,
  SetPlayingState,
  SetPlayingStateByUser,
  SetCurrentServiceProvider,
  SetTrackProgress,
  SetCanModifyVolume,
  SetMetaData,
  SetVolume,
  SetCanSeek,
  SetProviders,
  SetProviderIdentities,
  SetHasChangedPlaybackState,
  SetLastError,
}

type Action =
  | { type: AppActions.SetDefaultState }
  | { type: AppActions.SetDefaultMeta }
  | { type: AppActions.SetIsSeeking; value: boolean }
  | { type: AppActions.SeekToPosition; value: number }
  | { type: AppActions.SetPlayingState; value: string }
  | { type: AppActions.SetPlayingStateByUser; value: string }
  | { type: AppActions.SetIsAdjustingVolume; value: boolean }
  | { type: AppActions.AdjustVolumeByUser; value: number }
  | { type: AppActions.SetVolume; value: number }
  | { type: AppActions.SetHasChangedPlaybackState; value: boolean }
  | { type: AppActions.SetTrackProgress; value: number }
  | { type: AppActions.SetCanModifyVolume; value: boolean }
  | { type: AppActions.SetCanSeek; value: boolean }
  | { type: AppActions.SetProviders; value: string[] }
  | { type: AppActions.SetProviderIdentities; value: PlayerInfo[] }
  | { type: AppActions.SetCurrentServiceProvider; value: string }
  | { type: AppActions.SetMetaData; value: TrackMetadata }
  | { type: AppActions.SetLastError; value: string };

type Dispatch = (action: Action) => void;

const AppStateContext = createContext<{
  state: AppState;
  dispatch: Dispatch;
}>({
  state: defaultState,
  dispatch: () => null,
});

function mainReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case AppActions.SetDefaultState:
      return { ...state, ...defaultState };
    case AppActions.SetDefaultMeta:
      return { ...state, ...defaultMeta };
    case AppActions.SetIsSeeking:
      return { ...state, isSeeking: action.value };
    case AppActions.SetHasChangedPlaybackState:
      return { ...state, hasChangedPlaybackState: action.value };
    case AppActions.SetCanSeek:
      return { ...state, canSeek: action.value };
    case AppActions.SeekToPosition:
      return { ...state, currentTrackProgress: action.value, isSeeking: true };
    case AppActions.SetPlayingState:
      if (state.hasChangedPlaybackState) return state;
      return { ...state, currentTrackStatus: action.value };
    case AppActions.SetPlayingStateByUser:
      return {
        ...state,
        currentTrackStatus: action.value,
        hasChangedPlaybackState: true,
      };
    case AppActions.SetIsAdjustingVolume:
      return { ...state, isSettingVolume: action.value };
    case AppActions.SetProviders:
      return { ...state, providers: action.value };
    case AppActions.SetProviderIdentities:
      return { ...state, providersToIdentity: action.value };
    case AppActions.SetTrackProgress:
      if (state.isSeeking) return state;
      return {
        ...state,
        currentTrackProgress: Number.isFinite(action.value) ? action.value : 0,
      };
    case AppActions.SetCanModifyVolume:
      return { ...state, canModifyVolume: action.value };
    case AppActions.AdjustVolumeByUser:
      return { ...state, currentVolume: action.value, isSettingVolume: true };
    case AppActions.SetVolume:
      if (state.isSettingVolume) return state;
      return { ...state, currentVolume: action.value };
    case AppActions.SetCurrentServiceProvider: {
      const hasChanged = state.currentServiceProvider !== action.value;
      if (hasChanged) {
        return {
          ...state,
          currentServiceProvider: action.value,
          hasChangedProvider: true,
        };
      }
      return state;
    }
    case AppActions.SetMetaData: {
      const m = action.value;
      return {
        ...state,
        currentSong: m.title || defaultState.currentSong,
        currentArtist: m.artist || defaultState.currentArtist,
        currentArtUrl: m.artUrl || defaultState.currentArtUrl,
        hasAvailableTrack: Boolean(m.title || m.trackid || m.artUrl),
        currentTrackLength: m.length && m.length > 0 ? m.length : defaultState.currentTrackLength,
        currentTrackId: m.trackid || "",
      };
    }
    case AppActions.SetLastError:
      return { ...state, lastError: action.value };
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
