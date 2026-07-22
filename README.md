# MusicControl

Decky Loader plugin for controlling **MPRIS** media players from Steam Deck / Steam Machine Game Mode (Strawberry, Spotify, Firefox, and others).

Maintained rewrite of the archived [mirobouma/MusicControl](https://github.com/mirobouma/MusicControl).

## Usage

1. Install via Decky Loader.
2. Start your music app **from Game Mode** so it registers on the session D-Bus.
3. Open the Quick Access menu → **MusicControl**.
4. If multiple players are running, use the provider button to switch (selection is remembered).

## Supported players

Any app that implements [MPRIS MediaPlayer2.Player](https://specifications.freedesktop.org/mpris-spec/2.2/Player_Interface.html).

## Development

```bash
pnpm i
pnpm run build
python3 tests/test_metadata.py
```

## License

MIT (see `LICENSE`). Original plugin by Miro Bouma.
