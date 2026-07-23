/**
 * index.tsx
 * ---------
 * Frontend entry point for the Decky plugin.
 *
 * `@decky/rollup` builds this file into `dist/index.js` (IIFE / ESM as
 * configured). Decky Loader then loads that bundle when the user opens
 * the plugin list / Quick Access panel.
 *
 * `definePlugin` registers:
 *   * name / titleView / icon — how we appear in Decky menus
 *   * content — the React tree shown in the QAM plugin panel
 *   * onDismount — cleanup when the plugin UI is torn down
 */

import { definePlugin } from "@decky/api";
import { staticClasses } from "@decky/ui";
import { FaMusic } from "react-icons/fa";
import { Content } from "./components/content";
import { AppContextProvider } from "./context/context";

export default definePlugin(() => {
  return {
    name: "MusicControl",
    titleView: <div className={staticClasses.Title}>MusicControl</div>,
    content: (
      // Context wraps the whole panel so any child can read/dispatch state
      <AppContextProvider>
        <Content />
      </AppContextProvider>
    ),
    icon: <FaMusic />,
    onDismount() {
      // Interval timers are cleaned up inside Content's useEffect return.
      // Nothing global to tear down here.
    },
  };
});
