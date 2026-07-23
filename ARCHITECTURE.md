# Architecture map

This document is a table of contents for the heavily commented source.
Open the listed files for full explanations.

## Runtime flow (one UI poll tick)

```
QAM open
  → Content.tsx setInterval (1s)
    → backend.poll()          [@decky/api RPC]
      → Plugin.poll()         [main.py]
        → MprisClient.list_players()   [mpris_client.py]  (cached ~3s)
        → MprisClient.get_status()     [mpris_client.py]  (GetAll)
          → run_dbus_send()            [bus_discover.py]
          → parse_player_get_all()     [mpris_parse.py]
    → dispatch(SetSnapshot)   [context.tsx]
    → re-render children
```

## Python modules

| File | Role |
|------|------|
| `main.py` | Decky `Plugin` class — async RPC surface only |
| `bus_discover.py` | Find session bus; run `dbus-send` |
| `mpris_client.py` | Caching MPRIS client (list, status, controls, art) |
| `mpris_parse.py` | Parse dbus-send text → Python values |
| `settings_store.py` | Persist preferred player JSON |
| `mpris_util.py` | Typed-variant helpers (tests / future native D-Bus) |

## TypeScript modules

| File | Role |
|------|------|
| `src/index.tsx` | `definePlugin` entry |
| `src/backend.ts` | `callable(...)` wrappers → Python methods |
| `src/types.d.ts` | Shared types + asset module decls |
| `src/context/*` | React reducer state |
| `src/components/*` | Panel UI pieces |

## Why dbus-send?

Steam Deck + Decky sandbox: shelling to system `dbus-send` is more reliable
than vendored native D-Bus bindings for session-bus access. Tradeoff is text
parsing (`mpris_parse.py`) instead of typed messages.

## MPRIS units

* Position / length: **microseconds**
* Volume: **0.0 – 1.0**
* Track id: object path or string; required for seek (`SetPosition`)
