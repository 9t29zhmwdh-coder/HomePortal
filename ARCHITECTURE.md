# Architecture

## Overview

HomePortal renders one page from `portal.json` in the data folder and the
images in its `photos/` subfolder. An admin changes `portal.json` through the
settings page after logging in. FastAPI serves everything, Nginx sits in
front, Docker Compose runs the two containers.

```
app/
├── main.py       page, /photos, /media, /setup, /login, /logout, /healthz
├── settings.py   /settings and every POST that changes the portal
├── web.py        shared helpers: rendering, session lookup, CSRF check
├── store.py      portal.json: load, atomic save, one-time import of portal.yaml
├── auth.py       auth.json: Argon2 password hash, session key, login lockout
├── uploads.py    background uploads: decode, re-encode as JPEG, thumbnails
├── catalog.py    themes, fonts, patterns and bundled photos
├── i18n.py       English and German interface text
├── portal.py     legacy YAML reader (import only) and the photo folder
├── templates/    _base, index, settings, setup, login
└── static/       style.css, fonts.css, fonts/, backgrounds/
```

## Data folder

| File | Written by | Content |
|---|---|---|
| `portal.json` | settings page | site texts, appearance, links, access switch |
| `auth.json` (0600) | setup, password change | Argon2 hash, session signing key |
| `uploads/` | background upload | re-encoded JPEGs and thumbnails, random names |
| `photos/` | you | album pictures, only read |
| `portal.yaml` | you (1.2) | imported once if `portal.json` does not exist yet |

## Security model

- **Viewing** is open on the network by default; the admin can require the
  password for the page, the album and uploaded images.
- **Changing** needs a session: a signed, HttpOnly, SameSite=Strict cookie,
  valid 30 days. Every form also carries a per-session CSRF token.
- **Password**: at least 10 characters, stored as an Argon2 hash. Changing it
  rotates the signing key and ends every session.
- **Login lockout**: five failures per client address within five minutes.
  Nginx overwrites `X-Forwarded-For`, so the address cannot be forged from outside.
- **Links**: only `http(s)://host` URLs are accepted; Jinja autoescapes all text.
- **Files**: `/photos/{name}` and `/media/{name}` return a file only when the
  name is in the directory listing, so the request never builds a path.
- **Uploads**: at most 20 MB, decoded with Pillow (decompression-bomb limit
  60 megapixels), written again as JPEG, which drops EXIF and GPS.

## CI

`.github/workflows/ci.yml` runs ruff, the pytest suite with coverage, and a
Docker Compose smoke test against the real stack through Nginx: links, photos
and the stylesheet are served, setup and login work, a 3 MB upload passes
Nginx, and a forged `X-Forwarded-For` does not get around the lockout.
