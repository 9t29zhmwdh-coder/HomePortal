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

## v1.5.0, Live Tiles, Planned
- [ ] Home Assistant entity values (token stays on the server)
- [ ] Reachability of services (NAS, router, ...), clock, optional weather

## v1.6.0, Embedded Apps, Planned
- [ ] Apps as a tile or a whole tab, with a tested list of which apps allow embedding

## v2.0.0
- [ ] README repositioned from "page of links" to dashboard, everything above verified together

## Dual-Licensing Readiness

Assessed 2026-07-11: Community-only, not a Dual-Licensing candidate. HomePortal is a self-hosted personal homelab dashboard, single-user by design, in the same category as Homepage, Homer, Heimdall and Dashy, all of which stay fully open source rather than dual-licensed. No team, multi-tenant or enterprise dimension exists anywhere on the roadmap. Revisit only if a genuine multi-user/shared-household use case is scoped in.
