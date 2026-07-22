import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import {
  debugInfo,
  getStatus,
  listPlayers,
  ping,
  setPlayer,
} from "../backend";
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
  // Keep latest state for the interval without resetting the timer
  const stateRef = useRef(state);
  stateRef.current = state;

  const updateStatus = async () => {
    const s = stateRef.current;
    try {
      // Fast liveness check — if this fails, backend isn't loaded
      try {
        const pong = await ping();
        if (!pong?.ok) {
          dispatch({
            type: AppActions.SetLastError,
            value: "Backend ping returned not-ok. Reload plugins.",
          });
          return;
        }
      } catch (e) {
        dispatch({
          type: AppActions.SetLastError,
          value: `Backend not responding: ${
            e instanceof Error ? e.message : String(e)
          }. Reinstall from GitHub release v2.0.3 and Decky → Reload plugins. Check ~/homebrew/logs/MusicControl/`,
        });
        return;
      }

      const players = await listPlayers();
      // Defend against unexpected backend/bridge shapes
      const list = Array.isArray(players) ? players : [];
      const busNames = list
        .map((p) => (p && typeof p === "object" ? p.busName : ""))
        .filter(Boolean) as string[];
      dispatch({ type: AppActions.SetProviders, value: busNames });
      dispatch({ type: AppActions.SetProviderIdentities, value: list });

      if (busNames.length === 0) {
        dispatch({ type: AppActions.SetDefaultState });
        let detail =
          "No MPRIS players found. Start Strawberry from Game Mode with a track playing.";
        try {
          const dbg = await debugInfo();
          const bits = [
            `v${dbg.version || "2.0.3"}`,
            dbg.note || "(no discovery note)",
            dbg.busAddress ? `bus=${dbg.busAddress}` : "bus=(none)",
            `uid=${dbg.uid}`,
            dbg.dbusSend ? "dbus-send=ok" : "dbus-send=MISSING",
            dbg.players?.length ? `raw=${dbg.players.join(",")}` : "",
            dbg.error,
          ].filter(Boolean);
          detail = bits.join(" · ");
        } catch (e) {
          detail = `Backend debug_info failed: ${
            e instanceof Error ? e.message : String(e)
          }`;
        }
        dispatch({ type: AppActions.SetLastError, value: detail });
        return;
      }

      let active = s.currentServiceProvider;
      if (!active || !busNames.includes(active)) {
        active = busNames[0];
        dispatch({ type: AppActions.SetCurrentServiceProvider, value: active });
        await setPlayer(active);
      }

      const status = await getStatus();
      if (status.error) {
        dispatch({ type: AppActions.SetLastError, value: status.error });
      } else {
        dispatch({ type: AppActions.SetLastError, value: "" });
      }

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

      if (status.metadata && (status.hasTrack || Object.keys(status.metadata).length > 0)) {
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
    } catch (e) {
      dispatch({
        type: AppActions.SetLastError,
        value: `listPlayers/getStatus failed: ${
          e instanceof Error ? e.message : String(e)
        }. If this persists, you may still be running store MusicControl 1.1.x — install the fork into ~/homebrew/plugins/MusicControl.`,
      });
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
      <PanelSectionRow>
        <div
          style={{
            fontSize: "0.75em",
            opacity: 0.85,
            marginTop: "6px",
            wordBreak: "break-word",
            whiteSpace: "pre-wrap",
          }}
        >
          {state.lastError
            ? state.lastError
            : state.currentServiceProvider
              ? `Controlling: ${state.currentServiceProvider}`
              : "Status: waiting for backend…"}
        </div>
      </PanelSectionRow>
      <PanelSectionRow>
        <div style={{ fontSize: "0.7em", opacity: 0.55, marginTop: "4px" }}>
          MusicControl fork v2.0.3 (JobDestroyer/MusicControlol). If status stays
          on “waiting for backend”, the Python side did not load — reinstall the
          release zip and Reload plugins.
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
};
