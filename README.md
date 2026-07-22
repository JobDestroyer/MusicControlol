# MusicControl (maintained fork)

Decky Loader plugin that controls **any MPRIS media player** from Steam Deck / Steam Machine Game Mode — including **Strawberry**, Spotify, and Firefox.

This is a maintained rewrite of the archived [mirobouma/MusicControl](https://github.com/mirobouma/MusicControl) project.

## What was wrong with the original

The old plugin shelled out to `dbus-send` and scraped replies with `grep`/`sed`. That broke after Decky / SteamOS changes, and it mishandled Strawberry specifically:

- multi-artist metadata arrays
- object-path track IDs for seek
- local `file://` album art (normal for Strawberry)

## What this fork changes

| Area | Fix |
|------|-----|
| D-Bus | Real client via **jeepney** (pure Python, vendored in `py_modules/`) |
| API | Decky **`api_version: 1`** with normal instance methods |
| Frontend | Modern `@decky/api` + `@decky/ui` |
| Status poll | Single `get_status` snapshot instead of many fragile shell calls |
| Strawberry | Correct Metadata maps, `SetPosition(o,x)`, `file://` art caching |

## Usage

1. Install [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader).
2. Install this plugin (manual zip or store, depending on distribution).
3. **Start your music app from Game Mode** (add Strawberry / Spotify as a non-Steam game if needed) so it appears on the session D-Bus.
4. Open the Quick Access menu → MusicControl.
5. If several players are running, use the provider button to switch.

## Supported players

Any app that implements [MPRIS MediaPlayer2.Player](https://specifications.freedesktop.org/mpris-spec/2.2/Player_Interface.html), for example:

- Strawberry (Flatpak or native)
- Spotify (Flatpak)
- Firefox / Chromium with media
- Many other Linux players

## Development

```bash
pnpm i
pnpm run build          # frontend → dist/index.js
python3 tests/test_metadata.py
```

Plugin layout for Decky:

- `main.py` — Python backend
- `py_modules/jeepney` — vendored D-Bus library
- `dist/index.js` — built frontend
- `plugin.json` — metadata (`api_version: 1`)

### Manual install on Deck

Copy the plugin directory to:

```text
~/homebrew/plugins/MusicControl/
```

Include at least: `main.py`, `plugin.json`, `package.json`, `dist/`, `py_modules/`, `LICENSE`, `README.md`.

Restart Decky or reload plugins.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No Media Player Found | Start the player **from Game Mode**, not only Desktop Mode |
| Player runs but not listed | Confirm MPRIS: `busctl --user list \| grep mpris` in a terminal as user `deck` |
| Art missing (Strawberry) | Covers are local files; plugin copies them into Steam UI cache |
| Seek does nothing | Player must expose a valid `mpris:trackid` object path (Strawberry does) |

Plugin logs: `~/homebrew/logs/MusicControl/` (path may match the plugin folder name under Decky).

## License

MIT (see `LICENSE`). Original MusicControl by Miro Bouma; this fork rewrites the D-Bus backend and updates the Decky integration.
