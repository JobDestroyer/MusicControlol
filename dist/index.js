const manifest = {"name":"MusicControl"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const useQuickAccessVisible = api.useQuickAccessVisible;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(source, excluded) { if (source == null) return {}; var target = _objectWithoutPropertiesLoose(source, excluded); var key, i; if (Object.getOwnPropertySymbols) { var sourceSymbolKeys = Object.getOwnPropertySymbols(source); for (i = 0; i < sourceSymbolKeys.length; i++) { key = sourceSymbolKeys[i]; if (excluded.indexOf(key) >= 0) continue; if (!Object.prototype.propertyIsEnumerable.call(source, key)) continue; target[key] = source[key]; } } return target; }
function _objectWithoutPropertiesLoose(source, excluded) { if (source == null) return {}; var target = {}; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { if (excluded.indexOf(key) >= 0) continue; target[key] = source[key]; } } return target; }
function _extends() { _extends = Object.assign ? Object.assign.bind() : function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(obj, key, value) { key = _toPropertyKey(key); if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var {
        attr,
        size,
        title
      } = props,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaFastBackward (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M0 436V76c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12v151.9L235.5 71.4C256.1 54.3 288 68.6 288 96v131.9L459.5 71.4C480.1 54.3 512 68.6 512 96v320c0 27.4-31.9 41.7-52.5 24.6L288 285.3V416c0 27.4-31.9 41.7-52.5 24.6L64 285.3V436c0 6.6-5.4 12-12 12H12c-6.6 0-12-5.4-12-12z"},"child":[]}]})(props);
}function FaFastForward (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M512 76v360c0 6.6-5.4 12-12 12h-40c-6.6 0-12-5.4-12-12V284.1L276.5 440.6c-20.6 17.2-52.5 2.8-52.5-24.6V284.1L52.5 440.6C31.9 457.8 0 443.4 0 416V96c0-27.4 31.9-41.7 52.5-24.6L224 226.8V96c0-27.4 31.9-41.7 52.5-24.6L448 226.8V76c0-6.6 5.4-12 12-12h40c6.6 0 12 5.4 12 12z"},"child":[]}]})(props);
}function FaMusic (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M470.38 1.51L150.41 96A32 32 0 0 0 128 126.51v261.41A139 139 0 0 0 96 384c-53 0-96 28.66-96 64s43 64 96 64 96-28.66 96-64V214.32l256-75v184.61a138.4 138.4 0 0 0-32-3.93c-53 0-96 28.66-96 64s43 64 96 64 96-28.65 96-64V32a32 32 0 0 0-41.62-30.49z"},"child":[]}]})(props);
}function FaPause (props) {
  return GenIcon({"attr":{"viewBox":"0 0 448 512"},"child":[{"tag":"path","attr":{"d":"M144 479H48c-26.5 0-48-21.5-48-48V79c0-26.5 21.5-48 48-48h96c26.5 0 48 21.5 48 48v352c0 26.5-21.5 48-48 48zm304-48V79c0-26.5-21.5-48-48-48h-96c-26.5 0-48 21.5-48 48v352c0 26.5 21.5 48 48 48h96c26.5 0 48-21.5 48-48z"},"child":[]}]})(props);
}function FaPlay (props) {
  return GenIcon({"attr":{"viewBox":"0 0 448 512"},"child":[{"tag":"path","attr":{"d":"M424.4 214.7L72.4 6.6C43.8-10.3 0 6.1 0 47.9V464c0 37.5 40.7 60.1 72.4 41.3l352-208c31.4-18.5 31.5-64.1 0-82.6z"},"child":[]}]})(props);
}

/**
 * backend.ts
 * ----------
 * Thin TypeScript wrappers around the Python methods defined on
 * `Plugin` in main.py.
 *
 * How Decky RPC works (api_version 1):
 *   1. `@decky/api` connects to the loader using the plugin name from
 *      plugin.json ("MusicControl").
 *   2. `callable<[Args], Return>("method_name")` returns a function that,
 *      when called, asks the loader to run `Plugin.method_name(*args)` in
 *      the plugin's Python process and returns a Promise of the result.
 *
 * Method names must match the Python `async def` names exactly
 * (e.g. "play_pause", not "playPause").
 */
/**
 * Primary tick API: one round-trip for player list + current track status.
 * Prefer this over calling listPlayers + getStatus separately.
 */
const poll = callable("poll");
/** List active MPRIS players as { busName, identity }[]. */
callable("list_players");
/**
 * Select which player subsequent controls affect.
 * Also persists the choice on the Python side (settings_store).
 */
const setPlayer = callable("set_player");
/** Currently selected bus name (may be empty string). */
callable("get_player");
/** Status for the currently selected player only. */
callable("get_status");
/** Toggle play/pause. */
const playPause = callable("play_pause");
/** Skip forward one track. */
const nextTrack = callable("next_track");
/** Skip backward one track. */
const previousTrack = callable("previous_track");
/**
 * Seek to an absolute position.
 * @param position - Microseconds into the track (MPRIS unit).
 * @param trackId  - Must match the current mpris:trackid object path/string.
 */
const setPosition = callable("set_position");
/**
 * Set playback volume.
 * @param volume - 0.0 … 1.0
 */
const setVolume = callable("set_volume");
/**
 * Prepare cover art for Steam UI display.
 * Local file:// URLs are copied into a Steam-visible cache; https URLs pass through.
 */
const cacheAlbumArt = callable("cache_album_art");

var default_music = 'http://127.0.0.1:1337/plugins/MusicControl/assets/default_music-de70c8a5.png';

/**
 * defaultState.ts
 * ---------------
 * Initial / empty UI state for the MusicControl panel.
 *
 * `default_music.png` is the placeholder cover shown when nothing is playing
 * or art is unavailable. Rollup rewrites the import to a steamloopback URL.
 */
/**
 * Full React state shape for the panel.
 *
 * Interaction flags (isSeeking, isSettingVolume, hasChangedPlaybackState)
 * prevent the 1 Hz poll from overwriting the user's in-progress drag or
 * optimistic play/pause toggle until a short timeout expires.
 */
const defaultState = {
    /** True for ~1s after the user hits play/pause, so poll won't flip the icon back */
    hasChangedPlaybackState: false,
    /** True while the user is dragging the seek slider */
    isSeeking: false,
    /** True while the user is dragging the volume slider */
    isSettingVolume: false,
    /** True when metadata looks like a real track */
    hasAvailableTrack: false,
    currentSong: "Not Playing",
    currentArtist: "Unknown Artist",
    /** Cover art URL (steamloopback, https, or placeholder asset) */
    currentArtUrl: default_music,
    /** mpris:trackid — required for seek */
    currentTrackId: "",
    /** Position and length are stored in *microseconds* (MPRIS units) */
    currentTrackProgress: 0,
    currentTrackLength: 1,
    /** "Playing" | "Paused" | "Stopped" */
    currentTrackStatus: "Paused",
    /** Selected org.mpris.MediaPlayer2.* bus name */
    currentServiceProvider: "",
    /** Friendly Identity for the selected player */
    currentIdentity: "",
    /** Bus names for the provider menu */
    providers: [],
    /** Full player rows for identity lookup in the menu */
    providersToIdentity: [],
    /** 0.0 – 1.0 */
    currentVolume: 1.0,
    canModifyVolume: false,
    canSeek: false,
    /**
     * True when the last poll found no MPRIS players — drives the empty-state
     * copy ("Start a media player from Game Mode").
     */
    emptyHint: false,
};

/** Discriminated action types the reducer understands. */
var AppActions;
(function (AppActions) {
    /** Reset to empty / "not playing" defaults (no players online). */
    AppActions[AppActions["SetDefaultState"] = 0] = "SetDefaultState";
    /** Clear or set the "user is seeking" flag. */
    AppActions[AppActions["SetIsSeeking"] = 1] = "SetIsSeeking";
    /** User moved the seek slider — update position and set isSeeking. */
    AppActions[AppActions["SeekToPosition"] = 2] = "SeekToPosition";
    /** Clear or set the "user is adjusting volume" flag. */
    AppActions[AppActions["SetIsAdjustingVolume"] = 3] = "SetIsAdjustingVolume";
    /** User moved the volume slider. */
    AppActions[AppActions["AdjustVolumeByUser"] = 4] = "AdjustVolumeByUser";
    /** Optimistic play/pause icon flip after a button press. */
    AppActions[AppActions["SetPlayingStateByUser"] = 5] = "SetPlayingStateByUser";
    /** Clear the optimistic play/pause lock after a short delay. */
    AppActions[AppActions["SetHasChangedPlaybackState"] = 6] = "SetHasChangedPlaybackState";
    /** User picked a provider from the menu (optimistic selection). */
    AppActions[AppActions["SetActiveProvider"] = 7] = "SetActiveProvider";
    /**
     * Full frame from Python `poll()` — players list + status.
     * This is the hot path (~1 Hz while the panel is open).
     */
    AppActions[AppActions["SetSnapshot"] = 8] = "SetSnapshot";
})(AppActions || (AppActions = {}));
const AppStateContext = SP_REACT.createContext({
    state: defaultState,
    dispatch: () => null,
});
/**
 * Map backend metadata fields onto the UI state slice for the current track.
 * Missing fields fall back to the default "Not Playing" placeholders.
 */
function applyMetadata(meta) {
    return {
        currentSong: meta.title || defaultState.currentSong,
        currentArtist: meta.artist || defaultState.currentArtist,
        currentArtUrl: meta.artUrl || defaultState.currentArtUrl,
        hasAvailableTrack: Boolean(meta.title || meta.trackid || meta.artUrl),
        // length is microseconds; keep a minimum of 1 so the seek slider math
        // never divides by zero
        currentTrackLength: meta.length && meta.length > 0 ? meta.length : defaultState.currentTrackLength,
        currentTrackId: meta.trackid || "",
    };
}
function mainReducer(state, action) {
    switch (action.type) {
        case AppActions.SetDefaultState:
            return {
                ...defaultState,
                isSeeking: false,
                isSettingVolume: false,
                emptyHint: true,
            };
        case AppActions.SetIsSeeking:
            return { ...state, isSeeking: action.value };
        case AppActions.SetHasChangedPlaybackState:
            return { ...state, hasChangedPlaybackState: action.value };
        case AppActions.SeekToPosition:
            // Freeze poll-driven position updates until isSeeking is cleared
            return { ...state, currentTrackProgress: action.value, isSeeking: true };
        case AppActions.SetPlayingStateByUser:
            return {
                ...state,
                currentTrackStatus: action.value,
                hasChangedPlaybackState: true,
            };
        case AppActions.SetIsAdjustingVolume:
            return { ...state, isSettingVolume: action.value };
        case AppActions.AdjustVolumeByUser:
            return { ...state, currentVolume: action.value, isSettingVolume: true };
        case AppActions.SetActiveProvider:
            return { ...state, currentServiceProvider: action.value };
        case AppActions.SetSnapshot: {
            const { players, status } = action;
            const busNames = players.map((p) => p.busName);
            // Nothing online (or backend said available=false)
            if (!players.length || !status.available) {
                return {
                    ...defaultState,
                    emptyHint: true,
                    providers: busNames,
                    providersToIdentity: players,
                };
            }
            const meta = status.metadata || {};
            const next = {
                ...state,
                emptyHint: false,
                providers: busNames,
                providersToIdentity: players,
                currentServiceProvider: status.player || state.currentServiceProvider,
                currentIdentity: status.identity || "",
                canSeek: status.canSeek,
                canModifyVolume: status.canControlVolume,
                ...applyMetadata(meta),
            };
            // Respect in-flight user interactions — don't yank the icon/slider
            if (!state.hasChangedPlaybackState) {
                next.currentTrackStatus =
                    status.playbackStatus || state.currentTrackStatus;
            }
            if (!state.isSeeking) {
                next.currentTrackProgress = status.position || 0;
            }
            if (!state.isSettingVolume && status.canControlVolume) {
                next.currentVolume = status.volume;
            }
            return next;
        }
        default:
            return state;
    }
}
/** Provider that wraps the plugin panel content. */
const AppContextProvider = ({ children }) => {
    const [state, dispatch] = SP_REACT.useReducer(mainReducer, defaultState);
    return (SP_JSX.jsx(AppStateContext.Provider, { value: { state, dispatch }, children: children }));
};
/** Hook for child components — throws if used outside the provider. */
function useStateContext() {
    const context = SP_REACT.useContext(AppStateContext);
    if (context === undefined) {
        throw new Error("useStateContext must be used within AppContextProvider");
    }
    return context;
}

/**
 * style.ts
 * --------
 * Shared inline CSSProperties for the MusicControl panel.
 * Kept as plain objects (not CSS modules) so they work inside Steam's
 * CEF environment without extra loaders.
 */
/** Horizontal rule under the transport buttons. */
const musicControlDividerStyle = {
    content: "",
    bottom: "-0.5px",
    left: "0",
    right: "0",
    height: "1px",
    background: "#23262e",
    // Bleed past the panel padding so the line spans the full QAM width
    width: "calc(100% + 32px)",
    marginLeft: "-16px",
    marginRight: "-16px",
};
/** First (leftmost) transport button — no left margin. */
const musicControlButtonStyleFirst = {
    marginLeft: "0px",
    height: "30px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "5px 0px 0px 0px",
    minWidth: "0",
};
/** Subsequent transport buttons — small gap from the previous one. */
const musicControlButtonStyle = {
    marginLeft: "5px",
    height: "30px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "5px 0px 0px 0px",
    minWidth: "0",
};
/**
 * Title / artist text: fixed max width with ellipsis so long track names
 * don't push the album art or wrap awkwardly in the narrow QAM column.
 */
const musicControlFieldStyle = {
    width: "180px",
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
};

const AlbumArt = ({ albumArt }) => {
    // What we actually put in <img src> (may lag albumArt while caching)
    const [displayUrl, setDisplayUrl] = SP_REACT.useState(defaultState.currentArtUrl);
    SP_REACT.useEffect(() => {
        let cancelled = false;
        (async () => {
            // Nothing / placeholder — show default art
            if (!albumArt || albumArt === defaultState.currentArtUrl) {
                if (!cancelled)
                    setDisplayUrl(defaultState.currentArtUrl);
                return;
            }
            // Local file — must go through the backend cache
            if (albumArt.startsWith("file:") || albumArt.startsWith("file:///")) {
                try {
                    const cached = await cacheAlbumArt(albumArt);
                    if (!cancelled) {
                        setDisplayUrl(cached || defaultState.currentArtUrl);
                    }
                }
                catch {
                    if (!cancelled)
                        setDisplayUrl(defaultState.currentArtUrl);
                }
                return;
            }
            // Already a loadable URL (http/https/steamloopback)
            if (!cancelled)
                setDisplayUrl(albumArt);
        })();
        return () => {
            // Ignore late results if albumArt changed mid-flight
            cancelled = true;
        };
    }, [albumArt]);
    return (SP_JSX.jsx("div", { style: { width: "80px", height: "80px", flexShrink: 0 }, children: SP_JSX.jsx("img", { style: {
                borderRadius: "5px",
                width: "80px",
                height: "80px",
                objectFit: "cover",
            }, src: displayUrl, alt: "", onError: ({ currentTarget }) => {
                // Broken image URL → fall back to placeholder once
                if (currentTarget.src === defaultState.currentArtUrl)
                    return;
                currentTarget.src = defaultState.currentArtUrl;
            } }) }));
};

const ArtistInfoPanel = ({ title, artist, }) => {
    return (SP_JSX.jsxs("div", { style: { marginLeft: "10px", minWidth: 0 }, children: [SP_JSX.jsx("div", { style: { ...musicControlFieldStyle, fontWeight: 600 }, children: title }), SP_JSX.jsx("div", { style: { ...musicControlFieldStyle, opacity: 0.8, fontSize: "0.9em" }, children: artist })] }));
};

const MediaProviderButton = ({ currentProvider }) => {
    const { state, dispatch } = useStateContext();
    /** Prefer MPRIS Identity; fall back to the short bus-name suffix. */
    const displayName = (provider) => {
        const found = state.providersToIdentity.find((p) => p.busName === provider);
        if (found?.identity)
            return found.identity;
        return provider.replace("org.mpris.MediaPlayer2.", "");
    };
    const handleOnClick = (e) => DFL.showContextMenu(SP_JSX.jsx(DFL.Menu, { label: "Select Media Player", cancelText: "Cancel", children: state.providers.length === 0 ? (SP_JSX.jsx(DFL.MenuItem, { onSelected: () => undefined, children: "No players found" })) : (state.providers.map((provider) => (SP_JSX.jsx(DFL.MenuItem, { onSelected: () => {
                dispatch({
                    type: AppActions.SetActiveProvider,
                    value: provider,
                });
                void setPlayer(provider);
            }, children: displayName(provider) }, provider)))) }), 
    // Anchor the menu to the button (or window as last resort)
    e.currentTarget ?? window);
    const label = currentProvider === ""
        ? "No Media Player Found"
        : state.currentIdentity || displayName(currentProvider);
    return (SP_JSX.jsx(DFL.ButtonItem, { layout: "below", bottomSeparator: "none", onClick: handleOnClick, children: label }));
};

const MusicControls = () => {
    const { state, dispatch } = useStateContext();
    const timeoutRef = SP_REACT.useRef(null);
    const onPrevious = () => {
        void previousTrack();
    };
    const onPlayPause = () => {
        if (state.hasAvailableTrack) {
            if (timeoutRef.current != null)
                clearTimeout(timeoutRef.current);
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
    SP_REACT.useEffect(() => {
        return () => {
            if (timeoutRef.current != null)
                clearTimeout(timeoutRef.current);
        };
    }, []);
    return (SP_JSX.jsxs(DFL.Focusable, { style: { marginTop: "10px", marginBottom: "10px", display: "flex" }, "flow-children": "horizontal", children: [SP_JSX.jsx(DFL.DialogButton, { style: musicControlButtonStyleFirst, onClick: onPrevious, children: SP_JSX.jsx(FaFastBackward, { style: { marginTop: "-4px", display: "block" } }) }), SP_JSX.jsx(DFL.DialogButton, { style: musicControlButtonStyle, onClick: onPlayPause, children: state.currentTrackStatus === "Playing" ? (SP_JSX.jsx(FaPause, { style: { marginTop: "-4px", display: "block" } })) : (SP_JSX.jsx(FaPlay, { style: { marginTop: "-4px", display: "block" } })) }), SP_JSX.jsx(DFL.DialogButton, { style: musicControlButtonStyle, onClick: onNext, children: SP_JSX.jsx(FaFastForward, { style: { marginTop: "-4px", display: "block" } }) })] }));
};

const SongProgressSlider = () => {
    const { state, dispatch } = useStateContext();
    const seekTimeoutRef = SP_REACT.useRef(null);
    const onSliderChanged = (value) => {
        // value is 0..1 → absolute microseconds
        const roundedProgress = Math.round(value * state.currentTrackLength);
        void setPosition(roundedProgress, state.currentTrackId);
        dispatch({ type: AppActions.SeekToPosition, value: roundedProgress });
        // Hold the seek lock for 1.5s after the last drag event
        if (seekTimeoutRef.current != null)
            clearTimeout(seekTimeoutRef.current);
        seekTimeoutRef.current = setTimeout(() => {
            dispatch({ type: AppActions.SetIsSeeking, value: false });
        }, 1500);
    };
    SP_REACT.useEffect(() => {
        return () => {
            if (seekTimeoutRef.current != null)
                clearTimeout(seekTimeoutRef.current);
        };
    }, []);
    // Hide entirely when we don't know the track length yet
    if (state.currentTrackLength <= 1)
        return SP_JSX.jsx("div", {});
    return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.SliderField, { value: state.currentTrackProgress / state.currentTrackLength, min: 0, max: 1, step: 0.05, 
            // Disable if the player says it can't seek, or we lack a track id
            disabled: !state.canSeek || !state.currentTrackId, onChange: onSliderChanged }) }));
};

const VolumeControl = () => {
    const { state, dispatch } = useStateContext();
    const volumeTimeoutRef = SP_REACT.useRef(null);
    const onSliderChanged = (value) => {
        // SliderField gives 0..100; MPRIS wants 0.0..1.0
        const normalized = value / 100.0;
        void setVolume(normalized);
        dispatch({ type: AppActions.AdjustVolumeByUser, value: normalized });
        if (volumeTimeoutRef.current != null)
            clearTimeout(volumeTimeoutRef.current);
        volumeTimeoutRef.current = setTimeout(() => {
            dispatch({ type: AppActions.SetIsAdjustingVolume, value: false });
        }, 1500);
    };
    SP_REACT.useEffect(() => {
        return () => {
            if (volumeTimeoutRef.current != null)
                clearTimeout(volumeTimeoutRef.current);
        };
    }, []);
    if (!state.hasAvailableTrack || !state.canModifyVolume)
        return SP_JSX.jsx("div", {});
    return (SP_JSX.jsxs("div", { children: [SP_JSX.jsx("div", { style: { marginTop: "5px" }, className: DFL.staticClasses.PanelSectionTitle, children: "Playback Volume" }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.SliderField, { value: Math.round(state.currentVolume * 100), min: 0, max: 100, step: 1, onChange: onSliderChanged }) })] }));
};

/**
 * True when the Quick Access menu (and thus our panel) is on screen.
 * Defaults to true if the Decky hook is unavailable.
 */
function usePanelVisible() {
    try {
        if (typeof useQuickAccessVisible === "function") {
            return useQuickAccessVisible();
        }
    }
    catch {
        // Hook threw (very old loader) — keep polling
    }
    return true;
}
const Content = () => {
    const { state, dispatch } = useStateContext();
    const visible = usePanelVisible();
    // Stable ref so the interval always calls the latest updateStatus
    // without resetting the timer every render
    const updateCallback = SP_REACT.useRef(() => undefined);
    /** One poll tick: fetch snapshot from Python and push into React state. */
    const updateStatus = async () => {
        try {
            const snapshot = await poll();
            const players = Array.isArray(snapshot?.players) ? snapshot.players : [];
            const status = snapshot?.status;
            if (!status) {
                dispatch({ type: AppActions.SetDefaultState });
                return;
            }
            dispatch({ type: AppActions.SetSnapshot, players, status });
        }
        catch {
            // Network/backend blip — leave previous UI state, try again next second
        }
    };
    // Keep the ref pointed at the latest closure
    SP_REACT.useEffect(() => {
        updateCallback.current = () => {
            void updateStatus();
        };
    });
    // Start/stop the 1 Hz poll when visibility changes
    SP_REACT.useEffect(() => {
        if (!visible)
            return;
        const id = setInterval(() => updateCallback.current(), 1000);
        void updateStatus(); // immediate first paint
        return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [visible]);
    // Copy shown in the title slot when no track is active
    const emptyLabel = state.emptyHint
        ? "Start a media player from Game Mode"
        : "Not Playing";
    return (SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx("div", { className: DFL.staticClasses.PanelSectionTitle, children: "Currently Playing" }), SP_JSX.jsxs("div", { style: { display: "flex", marginBottom: "5px", alignItems: "center" }, children: [SP_JSX.jsx(AlbumArt, { albumArt: state.currentArtUrl }), SP_JSX.jsx(ArtistInfoPanel, { title: state.hasAvailableTrack ? state.currentSong : emptyLabel, artist: state.hasAvailableTrack
                            ? state.currentArtist
                            : state.currentIdentity || "" })] }), SP_JSX.jsx(SongProgressSlider, {}), SP_JSX.jsx(MusicControls, {}), SP_JSX.jsx("div", { style: musicControlDividerStyle }), SP_JSX.jsx(VolumeControl, {}), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(MediaProviderButton, { currentProvider: state.currentServiceProvider }) })] }));
};

var index = definePlugin(() => {
    return {
        name: "MusicControl",
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "MusicControl" }),
        content: (
        // Context wraps the whole panel so any child can read/dispatch state
        SP_JSX.jsx(AppContextProvider, { children: SP_JSX.jsx(Content, {}) })),
        icon: SP_JSX.jsx(FaMusic, {}),
        onDismount() {
            // Interval timers are cleaned up inside Content's useEffect return.
            // Nothing global to tear down here.
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map
