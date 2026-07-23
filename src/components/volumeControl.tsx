/**
 * volumeControl.tsx
 * -----------------
 * Player volume slider (0–100% in the UI, 0.0–1.0 on the wire).
 *
 * Hidden when the active player doesn't expose a writable Volume property
 * (`canModifyVolume` false — common for some browser MPRIS bridges).
 *
 * Same drag-lock pattern as the seek slider: `isSettingVolume` prevents
 * poll from overwriting the thumb mid-drag.
 */

import { PanelSectionRow, SliderField, staticClasses } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { setVolume } from "../backend";
import { AppActions, useStateContext } from "../context/context";

export const VolumeControl: FC = () => {
  const { state, dispatch } = useStateContext();
  const volumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onSliderChanged = (value: number) => {
    // SliderField gives 0..100; MPRIS wants 0.0..1.0
    const normalized = value / 100.0;
    void setVolume(normalized);
    dispatch({ type: AppActions.AdjustVolumeByUser, value: normalized });

    if (volumeTimeoutRef.current != null) clearTimeout(volumeTimeoutRef.current);
    volumeTimeoutRef.current = setTimeout(() => {
      dispatch({ type: AppActions.SetIsAdjustingVolume, value: false });
    }, 1500);
  };

  useEffect(() => {
    return () => {
      if (volumeTimeoutRef.current != null) clearTimeout(volumeTimeoutRef.current);
    };
  }, []);

  if (!state.hasAvailableTrack || !state.canModifyVolume) return <div />;

  return (
    <div>
      <div style={{ marginTop: "5px" }} className={staticClasses.PanelSectionTitle}>
        Playback Volume
      </div>
      <PanelSectionRow>
        <SliderField
          value={Math.round(state.currentVolume * 100)}
          min={0}
          max={100}
          step={1}
          onChange={onSliderChanged}
        />
      </PanelSectionRow>
    </div>
  );
};
