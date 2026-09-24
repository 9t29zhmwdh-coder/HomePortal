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

## Ideas, not scheduled
- [ ] Optional password protection for the page
- [ ] Mobile layout check on small phones

## Dual-Licensing Readiness

Assessed 2026-07-11: Community-only, not a Dual-Licensing candidate. HomePortal is a self-hosted personal homelab dashboard, single-user by design, in the same category as Homepage, Homer, Heimdall and Dashy, all of which stay fully open source rather than dual-licensed. No team, multi-tenant or enterprise dimension exists anywhere on the roadmap. Revisit only if a genuine multi-user/shared-household use case is scoped in.
