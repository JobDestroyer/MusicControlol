import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { getStatus, listPlayers, setPlayer } from "../backend";
import { AppActions, useStateContext } from "../context/context";
import { musicControlDividerStyle } from "../styles/style";
import { AlbumArt } from "./albumArt";
import { ArtistInfoPanel } from "./artistInfoPanel";
import { MediaProviderButton } from "./mediaProviderButton";
import { MusicControls } from "./musicControls";
import { SongProgressSlider } from "./songProgressSlider";
import { VolumeControl } from "./volumeControl";

export const Content: FC = () => {
  const { state, dispatch } = useStateContext();
  const updateCallback = useRef<() => void>(() => undefined);
  const stateRef = useRef(state);
  stateRef.current = state;

  const updateStatus = async () => {
    const s = stateRef.current;
    try {
      const players = await listPlayers();
      const list = Array.isArray(players) ? players : [];
      const busNames = list
        .map((p) => (p && typeof p === "object" ? p.busName : ""))
        .filter(Boolean) as string[];

      dispatch({ type: AppActions.SetProviders, value: busNames });
      dispatch({ type: AppActions.SetProviderIdentities, value: list });

      if (busNames.length === 0) {
        dispatch({ type: AppActions.SetDefaultState });
        return;
      }

      let active = s.currentServiceProvider;
      if (!active || !busNames.includes(active)) {
        active = busNames[0];
        dispatch({ type: AppActions.SetCurrentServiceProvider, value: active });
        await setPlayer(active);
      }

      const status = await getStatus();
      if (!status.available) {
        dispatch({ type: AppActions.SetDefaultMeta });
        return;
      }

      if (status.player && status.player !== s.currentServiceProvider) {
        dispatch({
          type: AppActions.SetCurrentServiceProvider,
          value: status.player,
        });
      }

      if (
        status.metadata &&
        (status.hasTrack || Object.keys(status.metadata).length > 0)
      ) {
        dispatch({ type: AppActions.SetMetaData, value: status.metadata });
      } else {
        dispatch({ type: AppActions.SetDefaultMeta });
      }

      if (!s.isSeeking) {
        dispatch({ type: AppActions.SetTrackProgress, value: status.position });
      }

      dispatch({ type: AppActions.SetPlayingState, value: status.playbackStatus });
      dispatch({ type: AppActions.SetCanSeek, value: status.canSeek });
      dispatch({
        type: AppActions.SetCanModifyVolume,
        value: status.canControlVolume,
      });

      if (status.canControlVolume && !s.isSettingVolume) {
        dispatch({ type: AppActions.SetVolume, value: status.volume });
      }
    } catch {
      // Backend unavailable or transient D-Bus error; retry next tick
    }
  };

  useEffect(() => {
    updateCallback.current = () => {
      void updateStatus();
    };
  });

  useEffect(() => {
    const id = setInterval(() => updateCallback.current(), 1000);
    void updateStatus();
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PanelSection>
      <div className={staticClasses.PanelSectionTitle}>Currently Playing</div>
      <div style={{ display: "flex", marginBottom: "5px", alignItems: "center" }}>
        <AlbumArt albumArt={state.currentArtUrl} />
        <ArtistInfoPanel title={state.currentSong} artist={state.currentArtist} />
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
