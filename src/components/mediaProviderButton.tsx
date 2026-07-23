/**
 * mediaProviderButton.tsx
 * -----------------------
 * Button that opens a context menu of active MPRIS players.
 *
 * Selecting an entry:
 *   1. Optimistically updates React state (SetActiveProvider) so the label
 *      changes immediately.
 *   2. Calls Python `set_player`, which also persists the choice to disk
 *      so the next session prefers the same app.
 *
 * When nothing is online the button still renders ("No Media Player Found")
 * so the panel layout stays stable.
 */

import {
  ButtonItem,
  Menu,
  MenuItem,
  showContextMenu,
} from "@decky/ui";
import type { FC } from "react";
import { setPlayer } from "../backend";
import { AppActions, useStateContext } from "../context/context";

type Props = {
  /** Currently selected bus name (may be "") */
  currentProvider: string;
};

export const MediaProviderButton: FC<Props> = ({ currentProvider }) => {
  const { state, dispatch } = useStateContext();

  /** Prefer MPRIS Identity; fall back to the short bus-name suffix. */
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
                dispatch({
                  type: AppActions.SetActiveProvider,
                  value: provider,
                });
                void setPlayer(provider);
              }}
            >
              {displayName(provider)}
            </MenuItem>
          ))
        )}
      </Menu>,
      // Anchor the menu to the button (or window as last resort)
      e.currentTarget ?? window
    );

  const label =
    currentProvider === ""
      ? "No Media Player Found"
      : state.currentIdentity || displayName(currentProvider);

  return (
    <ButtonItem layout="below" bottomSeparator="none" onClick={handleOnClick}>
      {label}
    </ButtonItem>
  );
};
