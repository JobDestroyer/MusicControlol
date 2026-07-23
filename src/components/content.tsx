/**
 * content.tsx
 * -----------
 * Root UI of the MusicControl Quick Access panel.
 *
 * Responsibilities:
 *   1. Poll the Python backend (~1 Hz) while the panel is visible.
 *   2. Dispatch a single SetSnapshot per successful poll.
 *   3. Compose presentational children (art, title, seek, controls, volume,
 *      provider picker).
 *
 * Visibility-aware polling:
 *   `useQuickAccessVisible` (Decky API v2) tells us whether the QAM is open.
 *   When the user closes the menu we stop the interval so we don't hammer
 *   D-Bus in the background. On older loaders the hook may be missing —
 *   we then poll always (safe fallback).
 */

import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { useQuickAccessVisible as useQAVisibleMaybe } from "@decky/api";
import { poll } from "../backend";
import { AppActions, useStateContext } from "../context/context";
import { musicControlDividerStyle } from "../styles/style";
import { AlbumArt } from "./albumArt";
import { ArtistInfoPanel } from "./artistInfoPanel";
import { MediaProviderButton } from "./mediaProviderButton";
import { MusicControls } from "./musicControls";
import { SongProgressSlider } from "./songProgressSlider";
import { VolumeControl } from "./volumeControl";

/**
 * True when the Quick Access menu (and thus our panel) is on screen.
 * Defaults to true if the Decky hook is unavailable.
 */
function usePanelVisible(): boolean {
  try {
    if (typeof useQAVisibleMaybe === "function") {
      return useQAVisibleMaybe();
    }
  } catch {
    // Hook threw (very old loader) — keep polling
  }
  return true;
}

export const Content: FC = () => {
  const { state, dispatch } = useStateContext();
  const visible = usePanelVisible();

  // Stable ref so the interval always calls the latest updateStatus
  // without resetting the timer every render
  const updateCallback = useRef<() => void>(() => undefined);

  /** One poll tick: fetch snapshot from Python and push into React state. */
  const updateStatus = async () => {
    try {
      const snapshot = await poll();
      const players = Array.isArray(snapshot?.players) ? snapshot.players : [];
      const status = snapshot?.status;
      if (!status) {
        dispatch({ type: AppActions.SetDefaultState });
        return;
      }
      dispatch({ type: AppActions.SetSnapshot, players, status });
    } catch {
      // Network/backend blip — leave previous UI state, try again next second
    }
  };

  // Keep the ref pointed at the latest closure
  useEffect(() => {
    updateCallback.current = () => {
      void updateStatus();
    };
  });

  // Start/stop the 1 Hz poll when visibility changes
  useEffect(() => {
    if (!visible) return;
    const id = setInterval(() => updateCallback.current(), 1000);
    void updateStatus(); // immediate first paint
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // Copy shown in the title slot when no track is active
  const emptyLabel = state.emptyHint
    ? "Start a media player from Game Mode"
    : "Not Playing";

  return (
    <PanelSection>
      <div className={staticClasses.PanelSectionTitle}>Currently Playing</div>

      {/* Cover + title/artist row */}
      <div style={{ display: "flex", marginBottom: "5px", alignItems: "center" }}>
        <AlbumArt albumArt={state.currentArtUrl} />
        <ArtistInfoPanel
          title={state.hasAvailableTrack ? state.currentSong : emptyLabel}
          artist={
            state.hasAvailableTrack
              ? state.currentArtist
              : state.currentIdentity || ""
          }
        />
      </div>

      {/* Seek bar (hidden when length unknown) */}
      <SongProgressSlider />

      {/* Prev / Play-Pause / Next */}
      <MusicControls />

      <div style={musicControlDividerStyle} />

      {/* Volume slider (hidden when player has no Volume property) */}
      <VolumeControl />

      {/* Dropdown to switch among concurrent MPRIS apps */}
      <PanelSectionRow>
        <MediaProviderButton currentProvider={state.currentServiceProvider} />
      </PanelSectionRow>
    </PanelSection>
  );
};
