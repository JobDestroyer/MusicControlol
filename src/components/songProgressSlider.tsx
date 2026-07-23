/**
 * songProgressSlider.tsx
 * ----------------------
 * Seek bar for the current track.
 *
 * Units: state stores MPRIS microseconds for both progress and length.
 * The SliderField is normalized to 0..1 for display; we convert back
 * to microseconds when calling setPosition.
 *
 * While the user drags (`isSeeking`), poll updates to position are
 * ignored so the thumb doesn't jump under their finger.
 */

import { PanelSectionRow, SliderField } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { setPosition } from "../backend";
import { AppActions, useStateContext } from "../context/context";

export const SongProgressSlider: FC = () => {
  const { state, dispatch } = useStateContext();
  const seekTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onSliderChanged = (value: number) => {
    // value is 0..1 → absolute microseconds
    const roundedProgress = Math.round(value * state.currentTrackLength);
    void setPosition(roundedProgress, state.currentTrackId);
    dispatch({ type: AppActions.SeekToPosition, value: roundedProgress });

    // Hold the seek lock for 1.5s after the last drag event
    if (seekTimeoutRef.current != null) clearTimeout(seekTimeoutRef.current);
    seekTimeoutRef.current = setTimeout(() => {
      dispatch({ type: AppActions.SetIsSeeking, value: false });
    }, 1500);
  };

  useEffect(() => {
    return () => {
      if (seekTimeoutRef.current != null) clearTimeout(seekTimeoutRef.current);
    };
  }, []);

  // Hide entirely when we don't know the track length yet
  if (state.currentTrackLength <= 1) return <div />;

  return (
    <PanelSectionRow>
      <SliderField
        value={state.currentTrackProgress / state.currentTrackLength}
        min={0}
        max={1}
        step={0.05}
        // Disable if the player says it can't seek, or we lack a track id
        disabled={!state.canSeek || !state.currentTrackId}
        onChange={onSliderChanged}
      />
    </PanelSectionRow>
  );
};
