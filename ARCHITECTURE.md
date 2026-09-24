# Architecture

## Overview

HomePortal renders tabs of tiles from `portal.json` in the data folder and the
images in its `photos/` subfolder. An admin changes `portal.json` through the
settings page after logging in. FastAPI serves everything, Nginx sits in
front, Docker Compose runs the two containers.

```
app/
├── main.py       /, /d/{tab}, /live/{tab}/{tile}, /photos, /media, /setup, /login, /logout, /healthz
├── settings.py   /settings: appearance, texts, tabs, uploads, access, password
├── editor.py     /edit/{tab}: layout (JSON), add, change and delete tiles
├── tiles.py      tile types, fixed sizes, free-spot search, layout validation
├── live.py       Home Assistant, status and weather values: timeouts, cache, parallel fetch
├── connections.py  connections.json: Home Assistant address and token
├── web.py        shared helpers: rendering, session lookup, CSRF check
├── store.py      portal.json: load, atomic save, schema migration
├── auth.py       auth.json: Argon2 password hash, session key, login lockout
├── uploads.py    background uploads: decode, re-encode as JPEG, thumbnails
├── catalog.py    themes, fonts, patterns and bundled photos
├── i18n.py       English and German interface text
├── portal.py     legacy YAML reader (import only) and the photo folder
├── templates/    _base, _tabs, _tiles, index, edit, tile_form, settings, setup, login
└── static/       style.css, fonts.css, fonts/, backgrounds/, js/editor.js, vendor/gridstack
```

## Data folder

| File | Written by | Content |
|---|---|---|
| `portal.json` | settings, edit mode | schema 2: site texts, appearance, access switch, tabs with their tiles |
| `auth.json` (0600) | setup, password change | Argon2 hash, session signing key |
| `connections.json` (0600) | settings, Connections | Home Assistant address and long-lived token |
| `uploads/` | background upload | re-encoded JPEGs and thumbnails, random names |
| `photos/` | you | album pictures, only read |
| `portal.yaml` | you (1.2) | imported once if `portal.json` does not exist yet |

## Tabs and tiles

The grid has six columns and a fixed row height. Every tile type has a list of
allowed sizes (see `tiles.py`); the editor offers only those, and the server
rejects a layout with a size not on the list, a tile outside the grid, two tiles
on the same cell, or a tile missing or listed twice. The page is plain CSS grid,
placed by `--x/--y/--w/--h`; on phones it folds into two columns with dense
flow. gridstack.js is loaded only on the edit page.

Schema 1 (1.3, a flat link list) and `portal.yaml` (1.2) are migrated once into
one tab: links as 1x1 tiles in reading order, the album as a 6x2 tile below.

## Live tiles

A tab's live tiles are fetched in parallel before the page renders, each with a
3-second timeout, so one slow service delays the page by at most that. Results
are cached (Home Assistant 10 s, status 20 s, weather 15 min). `live.js`
re-requests `/live/{tab}/{tile}` every 30 seconds while the page is visible and
swaps in the server-rendered tile; clocks tick in the browser.

- **Home Assistant**: `GET /api/states/<entity>` with the stored token. Entity
  ids must match `domain.object_id` before they are saved, so they cannot bend
  the request path.
- **Status**: a streamed `GET` that stops after the headers; any answer below
  500 counts as up. Certificates are not verified here, since home services
  often use self-signed ones and nothing is read.
- **App**: a streamed `GET` reads `X-Frame-Options` and CSP `frame-ancestors`;
  the tile embeds the app only if neither refuses the portal's origin, and
  otherwise explains why and links to it. Checked when the page renders,
  cached for ten minutes, never refreshed by `live.js`.
- **Weather**: Open-Meteo forecast API with the coordinates found by its
  geocoding API when the tile is saved.

## Security model

- **Viewing** is open on the network by default; the admin can require the
  password for the page, the album and uploaded images.
- **Layout saves** are `fetch` calls with the CSRF token in an `X-CSRF-Token`
  header; a cross-site page cannot send that header without a CORS preflight,
  which the app never answers.
- **Changing** needs a session: a signed, HttpOnly, SameSite=Strict cookie,
  valid 30 days. Every form also carries a per-session CSRF token.
- **Password**: at least 10 characters, stored as an Argon2 hash. Changing it
  rotates the signing key and ends every session.
- **Login lockout**: five failures per client address within five minutes.
  Nginx overwrites `X-Forwarded-For`, so the address cannot be forged from outside.
- **Own headers**: every response carries `X-Frame-Options: SAMEORIGIN`,
  `X-Content-Type-Options: nosniff` and `Referrer-Policy: same-origin`, so
  other sites cannot frame the settings page.
- **Home Assistant token**: stored apart from `portal.json`, never rendered; a
  changed address requires entering the token again, so a hijacked session
  cannot redirect it to another server.
- **Links**: only `http(s)://host` URLs are accepted; Jinja autoescapes all text.
- **Files**: `/photos/{name}` and `/media/{name}` return a file only when the
  name is in the directory listing, so the request never builds a path.
- **Uploads**: at most 20 MB, decoded with Pillow (decompression-bomb limit
  60 megapixels), written again as JPEG, which drops EXIF and GPS.

## CI

`.github/workflows/ci.yml` runs ruff, the pytest suite with coverage, and a
Docker Compose smoke test against the real stack through Nginx: links, photos
and the stylesheet are served, setup and login work, a 3 MB upload passes
Nginx, a tile layout saves only with the CSRF header, and a forged `X-Forwarded-For`
does not get around the lockout.
