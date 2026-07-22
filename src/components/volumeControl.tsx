import { PanelSectionRow, SliderField, staticClasses } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { setVolume } from "../backend";
import { AppActions, useStateContext } from "../context/context";

export const VolumeControl: FC = () => {
  const { state, dispatch } = useStateContext();
  const volumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onSliderChanged = (value: number) => {
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
