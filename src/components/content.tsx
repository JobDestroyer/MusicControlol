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

function usePanelVisible(): boolean {
  try {
    if (typeof useQAVisibleMaybe === "function") {
      return useQAVisibleMaybe();
    }
  } catch {
    /* older API */
  }
  return true;
}

export const Content: FC = () => {
  const { state, dispatch } = useStateContext();
  const visible = usePanelVisible();
  const updateCallback = useRef<() => void>(() => undefined);

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
      // transient; retry next interval
    }
  };

  useEffect(() => {
    updateCallback.current = () => {
      void updateStatus();
    };
  });

  useEffect(() => {
    if (!visible) return;
    const id = setInterval(() => updateCallback.current(), 1000);
    void updateStatus();
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const emptyLabel = state.emptyHint
    ? "Start a media player from Game Mode"
    : "Not Playing";

  return (
    <PanelSection>
      <div className={staticClasses.PanelSectionTitle}>Currently Playing</div>
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
      <SongProgressSlider />
      <MusicControls />
      <div style={musicControlDividerStyle} />
      <VolumeControl />
      <PanelSectionRow>
        <MediaProviderButton currentProvider={state.currentServiceProvider} />
      </PanelSectionRow>
    </PanelSection>
  );
};
