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
      <AppContextProvider>
        <Content />
      </AppContextProvider>
    ),
    icon: <FaMusic />,
    onDismount() {
      // nothing to clean up beyond React unmount
    },
  };
});
