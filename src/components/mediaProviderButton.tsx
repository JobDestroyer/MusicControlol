import {
  ButtonItem,
  Menu,
  MenuItem,
  showContextMenu,
} from "@decky/ui";
import type { FC } from "react";
import { setPlayer } from "../backend";
import { AppActions, useStateContext } from "../context/context";

type Props = { currentProvider: string };

export const MediaProviderButton: FC<Props> = ({ currentProvider }) => {
  const { state, dispatch } = useStateContext();

  const displayName = (provider: string) => {
    const found = state.providersToIdentity.find((p) => p.busName === provider);
    if (found?.identity) return found.identity;
    return provider.replace("org.mpris.MediaPlayer2.", "");
  };

  const handleOnClick = (e: MouseEvent) =>
    showContextMenu(
      <Menu label="Select Media Player" cancelText="Cancel">
        {state.providers.length === 0 ? (
          <MenuItem onSelected={() => undefined}>No players found</MenuItem>
        ) : (
          state.providers.map((provider) => (
            <MenuItem
              key={provider}
              onSelected={() => {
                void setPlayer(provider);
                dispatch({
                  type: AppActions.SetCurrentServiceProvider,
                  value: provider,
                });
              }}
            >
              {displayName(provider)}
            </MenuItem>
          ))
        )}
      </Menu>,
      e.currentTarget ?? window
    );

  return (
    <ButtonItem layout="below" bottomSeparator="none" onClick={handleOnClick}>
      {currentProvider === ""
        ? "No Media Player Found"
        : displayName(currentProvider)}
    </ButtonItem>
  );
};
