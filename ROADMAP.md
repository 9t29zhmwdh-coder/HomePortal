# Roadmap

## v0.1.0, Initial Import (2026-06-15)
- FastAPI backend
- Nginx reverse proxy config
- Docker Compose stack

## v0.2.0, First Working UI (2026-07-13)
- Landing page with quick links and a photo album widget (`app/templates/`, `app/static/`)
- Fixed a startup crash: v0.1.0 referenced a UI that was never actually committed

## v0.3.0, Planned
- [ ] Bookmark management UI
- [ ] Widget system (clock, weather, RSS)
- [ ] User authentication (optional, single-user)

## v0.4.0, Planned
- [ ] Theme editor
- [ ] Mobile-responsive layout
- [ ] Plugin API

## v1.0.0, Stable
- [ ] Full documentation
- [ ] One-command install script
- [ ] Health endpoint for monitoring

## Dual-Licensing Readiness

Assessed 2026-07-11: Community-only, not a Dual-Licensing candidate. HomePortal is a self-hosted personal homelab dashboard, single-user by design, in the same category as Homepage, Homer, Heimdall and Dashy, all of which stay fully open source rather than dual-licensed. No team, multi-tenant or enterprise dimension exists anywhere on the roadmap. Revisit only if a genuine multi-user/shared-household use case is scoped in.
