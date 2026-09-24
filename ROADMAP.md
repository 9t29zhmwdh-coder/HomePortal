# Roadmap

## v0.1.0, Initial Import (2026-06-15)
- FastAPI backend
- Nginx reverse proxy config
- Docker Compose stack

## v0.2.0, First Working UI (2026-07-13)
- Landing page with quick links and a photo album widget (`app/templates/`, `app/static/`)
- Fixed a startup crash: v0.1.0 referenced a UI that was never actually committed

## v1.2.0, Your Own Content (2026-09-24)
- Links, title and headings come from `portal.yaml` in the data folder; the album shows the images in `photos/`
- Edits show up on the next reload, no restart
- Unsafe link URLs are refused, photos are served only by exact name
- Fixed: the stylesheet never loaded through Nginx
- Health endpoint `/healthz`

## v1.3.0, Settings and Themes (2026-09-24)
- Settings page with admin login (Argon2, CSRF, lockout), first-start password setup
- Five themes, four drawn patterns, seven bundled CC0 photos, own background uploads (EXIF removed, HEIC supported)
- Five bundled fonts, English and German interface following the browser
- Optional password for viewing
- Fixed: login lockout behind Nginx would have hit every client at once

## v1.4.0, Grid and Tabs (2026-09-24)
- Six-column grid, tiles in fixed sizes per type, placed by drag and drop in an edit mode
- Tile types: link, note, photo album
- Several tabs, each its own page; managed in the settings
- Layout validated on the server; phones fold the grid into two columns

## v1.5.0, Live Tiles (2026-09-24)
- Home Assistant tile with one to eight entities; token stored apart and never sent to the browser
- Status tile: reachability and response time of any service
- Clock with time zone, weather from Open-Meteo (the only internet request, opt-in per tile)
- Refresh every 30 seconds without reloading

## v1.6.0, Embedded Apps (2026-09-24)
- Apps as a tile (2x2 to 6x4) or across a whole tab
- Instead of a list from memory, the portal checks each app's framing headers and explains a refusal with a button to open it; Home Assistant's setting verified in its source code

## v2.0.0, Dashboard (2026-09-24)
- README repositioned from "a page of links" to a home dashboard
- STRIDE threat model (`docs/THREAT_MODEL.md`), audit trail for every change, error references
- Dependencies pinned with hashes in `requirements.lock`, `pip-audit` on every pull request, CycloneDX SBOM on every release
- Session cookie gets the Secure flag behind a TLS proxy

## Known limitations
- [ ] No TLS in the bundled stack; a TLS proxy in front is documented but not included
- [ ] Logout does not revoke a copied session cookie; only a password change ends all sessions
- [ ] Behind a TLS proxy, the login lockout counts the proxy's address unless the proxy forwards the client address

## Ideas, not scheduled
- [ ] Optional TLS in the bundled Nginx with a certificate from the data folder
- [ ] Server-side session list with "log out everywhere"

## Dual-Licensing Readiness

Assessed 2026-07-11: Community-only, not a Dual-Licensing candidate. HomePortal is a self-hosted personal homelab dashboard, single-user by design, in the same category as Homepage, Homer, Heimdall and Dashy, all of which stay fully open source rather than dual-licensed. No team, multi-tenant or enterprise dimension exists anywhere on the roadmap. Revisit only if a genuine multi-user/shared-household use case is scoped in.
