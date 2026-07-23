/**
 * musicControls.tsx
 * -----------------
 * Previous / Play-Pause / Next transport buttons.
 *
 * Play-Pause is optimistic: we flip the icon immediately, then let the
 * backend catch up. `hasChangedPlaybackState` blocks the 1 Hz poll from
 * overwriting the icon for ~1 second so it doesn't flicker.
 */

import { DialogButton, Focusable } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { FaFastBackward, FaFastForward, FaPause, FaPlay } from "react-icons/fa";
import { nextTrack, playPause, previousTrack } from "../backend";
import { AppActions, useStateContext } from "../context/context";
import {
  musicControlButtonStyle,
  musicControlButtonStyleFirst,
} from "../styles/style";

export const MusicControls: FC = () => {
  const { state, dispatch } = useStateContext();
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onPrevious = () => {
    void previousTrack();
  };

  const onPlayPause = () => {
    if (state.hasAvailableTrack) {
      if (timeoutRef.current != null) clearTimeout(timeoutRef.current);
      // Optimistic UI flip
      dispatch({
        type: AppActions.SetPlayingStateByUser,
        value: state.currentTrackStatus === "Playing" ? "Paused" : "Playing",
      });
      // After 1s, allow poll-driven status to take over again
      timeoutRef.current = setTimeout(() => {
        dispatch({ type: AppActions.SetHasChangedPlaybackState, value: false });
      }, 1000);
    }
    void playPause();
  };

  const onNext = () => {
    void nextTrack();
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current != null) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <Focusable
      style={{ marginTop: "10px", marginBottom: "10px", display: "flex" }}
      flow-children="horizontal"
    >
      <DialogButton style={musicControlButtonStyleFirst} onClick={onPrevious}>
        <FaFastBackward style={{ marginTop: "-4px", display: "block" }} />
      </DialogButton>
      <DialogButton style={musicControlButtonStyle} onClick={onPlayPause}>
        {state.currentTrackStatus === "Playing" ? (
          <FaPause style={{ marginTop: "-4px", display: "block" }} />
        ) : (
          <FaPlay style={{ marginTop: "-4px", display: "block" }} />
        )}
      </DialogButton>
      <DialogButton style={musicControlButtonStyle} onClick={onNext}>
        <FaFastForward style={{ marginTop: "-4px", display: "block" }} />
      </DialogButton>
    </Focusable>
  );
};
