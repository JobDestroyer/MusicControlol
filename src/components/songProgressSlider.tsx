import { PanelSectionRow, SliderField } from "@decky/ui";
import { useEffect, useRef, type FC } from "react";
import { setPosition } from "../backend";
import { AppActions, useStateContext } from "../context/context";

export const SongProgressSlider: FC = () => {
  const { state, dispatch } = useStateContext();
  const seekTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onSliderChanged = (value: number) => {
    const roundedProgress = Math.round(value * state.currentTrackLength);
    void setPosition(roundedProgress, state.currentTrackId);
    dispatch({ type: AppActions.SeekToPosition, value: roundedProgress });

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

  if (state.currentTrackLength <= 1) return <div />;

  return (
    <PanelSectionRow>
      <SliderField
        value={state.currentTrackProgress / state.currentTrackLength}
        min={0}
        max={1}
        step={0.05}
        disabled={!state.canSeek || !state.currentTrackId}
        onChange={onSliderChanged}
      />
    </PanelSectionRow>
  );
};
