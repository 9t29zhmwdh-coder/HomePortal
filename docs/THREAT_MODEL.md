# Threat Model

STRIDE analysis for Home Portal 2.0.0, following
[`standards/security.md`](https://github.com/9t29zhmwdh-coder/engineering-standards/blob/main/standards/security.md)
section 1. Revisit it whenever a new tile type, connection or data flow is added.

## System Overview

```
Browser on the home network
     |  HTTP (HTTPS if a TLS proxy sits in front)
     v
Nginx (container, port 80)
     |  HTTP, internal Docker network only
     v
FastAPI app (container) ---- DATA_PATH on the host
     |      |       |          portal.json, auth.json, connections.json,
     |      |       |          uploads/, photos/
     |      |       +--> Home Assistant REST API     (B4, token)
     |      +----------> any address of a status or app tile (B5, no credentials)
     +-----------------> Open-Meteo, internet          (B6, only with a weather tile)

Browser ---------------> embedded apps, loaded directly (B7)
```

## Trust Boundaries

| Boundary | Between | Authentication |
|---|---|---|
| B1 | Browser and Nginx | None for viewing by default; optional password for viewing. Changes need the admin session cookie plus a CSRF token |
| B2 | Nginx and app | Docker network; the app port is `expose`d, not published, so only Nginx reaches it |
| B3 | App and data folder | File system permissions; `auth.json` and `connections.json` are mode 0600 |
| B4 | App and Home Assistant | Long-lived access token in an `Authorization: Bearer` header |
| B5 | App and status/app targets | None; a streamed `GET` that stops after the headers |
| B6 | App and Open-Meteo | None; public API, coordinates only |
| B7 | Browser and embedded apps | Whatever the app itself requires; the portal passes nothing |

## STRIDE Analysis

### Spoofing

| Threat | Component | Mitigation |
|---|---|---|
| Someone on the network guesses the admin password | B1 | Argon2 hash, at least 10 characters, lockout after five failures per client address for five minutes, every attempt in the audit log |
| A forged client address dodges the lockout | B1, B2 | Nginx overwrites `X-Forwarded-For` with the real peer address; CI checks that a forged header does not help |
| A forged session cookie | B1 | Cookies are signed with a random key from `auth.json`; changing the password rotates the key |
| The first visitor after installation claims the admin account | B1 | Documented: set the password right after `docker compose up`. Accepted risk on a home network |

### Tampering

| Threat | Component | Mitigation |
|---|---|---|
| Another site submits a settings form in the admin's browser | B1 | SameSite=Strict cookie plus a per-session CSRF token on every form; layout saves need the token in a custom header, which a cross-site page cannot send without a CORS preflight |
| A crafted layout overlaps tiles or leaves the grid | B1 | Server validates every layout: each tile once, allowed sizes only, inside the grid, no overlap |
| An upload replaces files outside `uploads/` | B3 | Uploads get random names; served files are looked up in the directory listing, never built from the request path |
| A swapped dependency in the image build | Build | `requirements.lock` pins every package with its hash; `pip install --require-hashes` refuses anything else |

### Repudiation

| Threat | Component | Mitigation |
|---|---|---|
| Nobody can tell who changed the portal or when | App | Every POST to setup, login, logout, settings and edit mode writes a JSON audit line to stdout: actor, action, client address, time, outcome. Form contents are never logged. The app can only append to stdout |

### Information Disclosure

| Threat | Component | Mitigation |
|---|---|---|
| The Home Assistant token leaks through a page or backup of the settings | B3, B4 | Stored in `connections.json` (0600), apart from `portal.json`; never rendered; the form shows only whether one is stored |
| A stolen session points the stored token at another server | B4 | Changing the address requires entering the token again |
| Location data in uploaded photos | B3 | Uploads are decoded and written again as JPEG, which drops EXIF including GPS |
| Error details reveal paths or internals | App | Visitors get "Something went wrong. Reference: ..." ; the details go to the log under that reference |
| Photos visible to anyone on the network | B1 | Optional password for viewing covers the page, the album and uploads |
| Password and cookie readable on the wire | B1 | **Residual risk:** the stack serves plain HTTP. On a home network this is the usual setup; for anything beyond it, put a TLS proxy in front. The cookie then gets the Secure flag automatically |

### Denial of Service

| Threat | Component | Mitigation |
|---|---|---|
| A slow Home Assistant or status target stalls the page | B4, B5 | 3-second timeout per request, all tiles of a tab fetched in parallel, results cached |
| A huge or decompression-bomb upload | B3 | 20 MB limit in the app and in Nginx, 60-megapixel decode limit |
| Login lockout used to lock the admin out | B1 | Lockout is per client address, not global |

### Elevation of Privilege

| Threat | Component | Mitigation |
|---|---|---|
| A viewer reaches a settings or edit route directly | B1 | Every change route depends on the session check; tests cover each without a session |
| Script injection through a link, note, tab name or Home Assistant name | B1 | Jinja autoescaping everywhere; link and app addresses must be `http(s)://host`; notes are plain text |
| Another site frames the settings page to trick clicks | B1 | `X-Frame-Options: SAMEORIGIN` on every response |
| The admin makes the server request internal addresses | B5 | By design: status and app tiles exist to check local services. Only the admin can add them; nothing is read beyond the headers |

## Residual Risks

- **No TLS by default.** Documented in the README with the TLS proxy setup; tracked in `ROADMAP.md`.
- **Logout does not revoke a copied cookie.** Sessions are signed, not stored, so a cookie copied before logout stays valid for up to 30 days unless the password is changed, which ends every session. Tracked in `ROADMAP.md`.
- **Token at rest in plain text.** `connections.json` is 0600, but anyone with root on the host can read it. Encrypting it would need a key stored next to it, which adds no protection.
- **Behind a TLS proxy, the lockout sees the proxy's address**, so failures from all clients count together. The proxy should pass the real client address, or its own rate limit should apply.
- **Embedded apps run without a sandbox**, since most apps need scripts, forms and cookies. Only the admin chooses which apps are embedded.
