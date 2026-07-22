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

const listPlayers = callable("list_players");
const setPlayer = callable("set_player");
callable("get_player");
const getStatus = callable("get_status");
const playPause = callable("play_pause");
const nextTrack = callable("next_track");
const previousTrack = callable("previous_track");
const setPosition = callable("set_position");
const setVolume = callable("set_volume");
const cacheAlbumArt = callable("cache_album_art");
const debugInfo = callable("debug_info");

var default_music = 'http://127.0.0.1:1337/plugins/MusicControl/assets/default_music-de70c8a5.png';

const defaultState = {
    hasChangedPlaybackState: false,
    hasChangedProvider: true,
    isSeeking: false,
    isSettingVolume: false,
    hasAvailableTrack: false,
    currentSong: "Not Playing",
    currentArtist: "Unknown Artist",
    currentArtUrl: default_music,
    currentTrackId: "",
    currentTrackProgress: 0,
    currentTrackLength: 1,
    currentTrackStatus: "Paused",
    currentServiceProvider: "",
    providers: [],
    providersToIdentity: [],
    currentVolume: 1.0,
    canModifyVolume: false,
    canSeek: false,
    lastError: "",
};
const defaultMeta = {
    hasAvailableTrack: false,
    hasChangedPlaybackState: false,
    isSeeking: false,
    isSettingVolume: false,
    currentSong: "Not Playing",
    currentArtist: "Unknown Artist",
    currentArtUrl: default_music,
    currentTrackId: "",
    currentTrackProgress: 0,
    currentTrackLength: 1,
    currentTrackStatus: "Paused",
    currentVolume: 1.0,
    canModifyVolume: false,
    canSeek: false,
};

var AppActions;
(function (AppActions) {
    AppActions[AppActions["SetDefaultState"] = 0] = "SetDefaultState";
    AppActions[AppActions["SetDefaultMeta"] = 1] = "SetDefaultMeta";
    AppActions[AppActions["SetIsSeeking"] = 2] = "SetIsSeeking";
    AppActions[AppActions["SeekToPosition"] = 3] = "SeekToPosition";
    AppActions[AppActions["SetIsAdjustingVolume"] = 4] = "SetIsAdjustingVolume";
    AppActions[AppActions["AdjustVolumeByUser"] = 5] = "AdjustVolumeByUser";
    AppActions[AppActions["SetPlayingState"] = 6] = "SetPlayingState";
    AppActions[AppActions["SetPlayingStateByUser"] = 7] = "SetPlayingStateByUser";
    AppActions[AppActions["SetCurrentServiceProvider"] = 8] = "SetCurrentServiceProvider";
    AppActions[AppActions["SetTrackProgress"] = 9] = "SetTrackProgress";
    AppActions[AppActions["SetCanModifyVolume"] = 10] = "SetCanModifyVolume";
    AppActions[AppActions["SetMetaData"] = 11] = "SetMetaData";
    AppActions[AppActions["SetVolume"] = 12] = "SetVolume";
    AppActions[AppActions["SetCanSeek"] = 13] = "SetCanSeek";
    AppActions[AppActions["SetProviders"] = 14] = "SetProviders";
    AppActions[AppActions["SetProviderIdentities"] = 15] = "SetProviderIdentities";
    AppActions[AppActions["SetHasChangedPlaybackState"] = 16] = "SetHasChangedPlaybackState";
    AppActions[AppActions["SetLastError"] = 17] = "SetLastError";
})(AppActions || (AppActions = {}));
const AppStateContext = SP_REACT.createContext({
    state: defaultState,
    dispatch: () => null,
});
function mainReducer(state, action) {
    switch (action.type) {
        case AppActions.SetDefaultState:
            return { ...state, ...defaultState };
        case AppActions.SetDefaultMeta:
            return { ...state, ...defaultMeta };
        case AppActions.SetIsSeeking:
            return { ...state, isSeeking: action.value };
        case AppActions.SetHasChangedPlaybackState:
            return { ...state, hasChangedPlaybackState: action.value };
        case AppActions.SetCanSeek:
            return { ...state, canSeek: action.value };
        case AppActions.SeekToPosition:
            return { ...state, currentTrackProgress: action.value, isSeeking: true };
        case AppActions.SetPlayingState:
            if (state.hasChangedPlaybackState)
                return state;
            return { ...state, currentTrackStatus: action.value };
        case AppActions.SetPlayingStateByUser:
            return {
                ...state,
                currentTrackStatus: action.value,
                hasChangedPlaybackState: true,
            };
        case AppActions.SetIsAdjustingVolume:
            return { ...state, isSettingVolume: action.value };
        case AppActions.SetProviders:
            return { ...state, providers: action.value };
        case AppActions.SetProviderIdentities:
            return { ...state, providersToIdentity: action.value };
        case AppActions.SetTrackProgress:
            if (state.isSeeking)
                return state;
            return {
                ...state,
                currentTrackProgress: Number.isFinite(action.value) ? action.value : 0,
            };
        case AppActions.SetCanModifyVolume:
            return { ...state, canModifyVolume: action.value };
        case AppActions.AdjustVolumeByUser:
            return { ...state, currentVolume: action.value, isSettingVolume: true };
        case AppActions.SetVolume:
            if (state.isSettingVolume)
                return state;
            return { ...state, currentVolume: action.value };
        case AppActions.SetCurrentServiceProvider: {
            const hasChanged = state.currentServiceProvider !== action.value;
            if (hasChanged) {
                return {
                    ...state,
                    currentServiceProvider: action.value,
                    hasChangedProvider: true,
                };
            }
            return state;
        }
        case AppActions.SetMetaData: {
            const m = action.value;
            return {
                ...state,
                currentSong: m.title || defaultState.currentSong,
                currentArtist: m.artist || defaultState.currentArtist,
                currentArtUrl: m.artUrl || defaultState.currentArtUrl,
                hasAvailableTrack: Boolean(m.title || m.trackid || m.artUrl),
                currentTrackLength: m.length && m.length > 0 ? m.length : defaultState.currentTrackLength,
                currentTrackId: m.trackid || "",
            };
        }
        case AppActions.SetLastError:
            return { ...state, lastError: action.value };
        default:
            return state;
    }
}
const AppContextProvider = ({ children }) => {
    const [state, dispatch] = SP_REACT.useReducer(mainReducer, defaultState);
    return (SP_JSX.jsx(AppStateContext.Provider, { value: { state, dispatch }, children: children }));
};
function useStateContext() {
    const context = SP_REACT.useContext(AppStateContext);
    if (context === undefined) {
        throw new Error("useStateContext must be used within AppContextProvider");
    }
    return context;
}

const musicControlDividerStyle = {
    content: "",
    bottom: "-0.5px",
    left: "0",
    right: "0",
    height: "1px",
    background: "#23262e",
    width: "calc(100% + 32px)",
    marginLeft: "-16px",
    marginRight: "-16px",
};
const musicControlButtonStyleFirst = {
    marginLeft: "0px",
    height: "30px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "5px 0px 0px 0px",
    minWidth: "0",
};
const musicControlButtonStyle = {
    marginLeft: "5px",
    height: "30px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "5px 0px 0px 0px",
    minWidth: "0",
};
const musicControlFieldStyle = {
    width: "180px",
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
};

const AlbumArt = ({ albumArt }) => {
    const [displayUrl, setDisplayUrl] = SP_REACT.useState(defaultState.currentArtUrl);
    SP_REACT.useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!albumArt || albumArt === defaultState.currentArtUrl) {
                if (!cancelled)
                    setDisplayUrl(defaultState.currentArtUrl);
                return;
            }
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
            if (!cancelled)
                setDisplayUrl(albumArt);
        })();
        return () => {
            cancelled = true;
        };
    }, [albumArt]);
    return (SP_JSX.jsx("div", { style: { width: "80px", height: "80px", flexShrink: 0 }, children: SP_JSX.jsx("img", { style: { borderRadius: "5px", width: "80px", height: "80px", objectFit: "cover" }, src: displayUrl, alt: "", onError: ({ currentTarget }) => {
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
    const displayName = (provider) => {
        const found = state.providersToIdentity.find((p) => p.busName === provider);
        if (found?.identity)
            return found.identity;
        return provider.replace("org.mpris.MediaPlayer2.", "");
    };
    const handleOnClick = (e) => DFL.showContextMenu(SP_JSX.jsx(DFL.Menu, { label: "Select Media Player", cancelText: "Cancel", children: state.providers.length === 0 ? (SP_JSX.jsx(DFL.MenuItem, { onSelected: () => undefined, children: "No players found" })) : (state.providers.map((provider) => (SP_JSX.jsx(DFL.MenuItem, { onSelected: () => {
                void setPlayer(provider);
                dispatch({
                    type: AppActions.SetCurrentServiceProvider,
                    value: provider,
                });
            }, children: displayName(provider) }, provider)))) }), e.currentTarget ?? window);
    return (SP_JSX.jsx(DFL.ButtonItem, { layout: "below", bottomSeparator: "none", onClick: handleOnClick, children: currentProvider === ""
            ? "No Media Player Found"
            : displayName(currentProvider) }));
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
            dispatch({
                type: AppActions.SetPlayingStateByUser,
                value: state.currentTrackStatus === "Playing" ? "Paused" : "Playing",
            });
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
        const roundedProgress = Math.round(value * state.currentTrackLength);
        void setPosition(roundedProgress, state.currentTrackId);
        dispatch({ type: AppActions.SeekToPosition, value: roundedProgress });
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
    if (state.currentTrackLength <= 1)
        return SP_JSX.jsx("div", {});
    return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.SliderField, { value: state.currentTrackProgress / state.currentTrackLength, min: 0, max: 1, step: 0.05, disabled: !state.canSeek || !state.currentTrackId, onChange: onSliderChanged }) }));
};

const VolumeControl = () => {
    const { state, dispatch } = useStateContext();
    const volumeTimeoutRef = SP_REACT.useRef(null);
    const onSliderChanged = (value) => {
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

const Content = () => {
    const { state, dispatch } = useStateContext();
    const updateCallback = SP_REACT.useRef(() => undefined);
    // Keep latest state for the interval without resetting the timer
    const stateRef = SP_REACT.useRef(state);
    stateRef.current = state;
    const updateStatus = async () => {
        const s = stateRef.current;
        try {
            const players = await listPlayers();
            const busNames = players.map((p) => p.busName);
            dispatch({ type: AppActions.SetProviders, value: busNames });
            dispatch({ type: AppActions.SetProviderIdentities, value: players });
            if (busNames.length === 0) {
                dispatch({ type: AppActions.SetDefaultState });
                let detail = "No MPRIS players found. Start Strawberry from Game Mode and wait until music is playing.";
                try {
                    const dbg = await debugInfo();
                    const bits = [
                        dbg.note,
                        dbg.busAddress ? `bus=${dbg.busAddress}` : "",
                        dbg.dbusSend ? "" : "dbus-send missing",
                        dbg.error,
                    ].filter(Boolean);
                    if (bits.length)
                        detail = bits.join(" · ");
                }
                catch {
                    /* keep default */
                }
                dispatch({ type: AppActions.SetLastError, value: detail });
                return;
            }
            let active = s.currentServiceProvider;
            if (!active || !busNames.includes(active)) {
                active = busNames[0];
                dispatch({ type: AppActions.SetCurrentServiceProvider, value: active });
                await setPlayer(active);
            }
            const status = await getStatus();
            if (status.error) {
                dispatch({ type: AppActions.SetLastError, value: status.error });
            }
            else {
                dispatch({ type: AppActions.SetLastError, value: "" });
            }
            if (!status.available) {
                dispatch({ type: AppActions.SetDefaultMeta });
                return;
            }
            if (status.player && status.player !== s.currentServiceProvider) {
                dispatch({
                    type: AppActions.SetCurrentServiceProvider,
                    value: status.player,
                });
            }
            if (status.metadata && (status.hasTrack || Object.keys(status.metadata).length > 0)) {
                dispatch({ type: AppActions.SetMetaData, value: status.metadata });
            }
            else {
                dispatch({ type: AppActions.SetDefaultMeta });
            }
            if (!s.isSeeking) {
                dispatch({ type: AppActions.SetTrackProgress, value: status.position });
            }
            dispatch({ type: AppActions.SetPlayingState, value: status.playbackStatus });
            dispatch({ type: AppActions.SetCanSeek, value: status.canSeek });
            dispatch({
                type: AppActions.SetCanModifyVolume,
                value: status.canControlVolume,
            });
            if (status.canControlVolume && !s.isSettingVolume) {
                dispatch({ type: AppActions.SetVolume, value: status.volume });
            }
        }
        catch (e) {
            dispatch({
                type: AppActions.SetLastError,
                value: e instanceof Error ? e.message : String(e),
            });
        }
    };
    SP_REACT.useEffect(() => {
        updateCallback.current = () => {
            void updateStatus();
        };
    });
    SP_REACT.useEffect(() => {
        const id = setInterval(() => updateCallback.current(), 1000);
        void updateStatus();
        return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    return (SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx("div", { className: DFL.staticClasses.PanelSectionTitle, children: "Currently Playing" }), SP_JSX.jsxs("div", { style: { display: "flex", marginBottom: "5px", alignItems: "center" }, children: [SP_JSX.jsx(AlbumArt, { albumArt: state.currentArtUrl }), SP_JSX.jsx(ArtistInfoPanel, { title: state.currentSong, artist: state.currentArtist })] }), SP_JSX.jsx(SongProgressSlider, {}), SP_JSX.jsx(MusicControls, {}), SP_JSX.jsx("div", { style: musicControlDividerStyle }), SP_JSX.jsx(VolumeControl, {}), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(MediaProviderButton, { currentProvider: state.currentServiceProvider }) }), state.lastError ? (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: "0.8em", opacity: 0.75, marginTop: "4px" }, children: state.lastError }) })) : null, SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx("div", { style: { fontSize: "0.75em", opacity: 0.6, marginTop: "8px" }, children: "Start players from Game Mode so they share the session D-Bus. Works with Strawberry, Spotify, Firefox, and other MPRIS apps." }) })] }));
};

var index = definePlugin(() => {
    return {
        name: "MusicControl",
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "MusicControl" }),
        content: (SP_JSX.jsx(AppContextProvider, { children: SP_JSX.jsx(Content, {}) })),
        icon: SP_JSX.jsx(FaMusic, {}),
        onDismount() {
            // nothing to clean up beyond React unmount
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map
