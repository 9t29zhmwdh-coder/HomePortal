# Changelog

All notable changes to HomePortal will be documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.2.0] - 2026-07-13

### Fixed

- Fixed a startup crash: `app/main.py` referenced a `static/` directory and an `app/templates/index.html` file that did not exist anywhere in the repository, so the app failed with `RuntimeError: Directory 'static' does not exist` on every launch.
- Made `StaticFiles`/`Jinja2Templates` directory paths resolve relative to `app/main.py`'s own location instead of the process's current working directory.
- Updated the `TemplateResponse` call for the current Starlette API, which now takes `request` as its first argument.

### Added

- Built the actual landing page: a Quick Links grid and a Family Album widget with demo placeholder photos, plus matching CSS.
- Added a smoke test suite (`tests/test_smoke.py`) and a `pytest.ini` so CI catches this class of bug in the future.
- Added a real screenshot (`docs/screenshot.png`) of the running app to both README files.
- Added "How it runs" / "In practice" / "Uninstall" sections to README.md and README.de.md.

## [0.1.5] - 2026-07-12

### Fixed

- Removed an eszett and em-dashes across the repo (TEMPLATE_NOTES.md, GETTING_STARTED.md, LICENSE, SKELETON.md). Swiss German orthography.

## [0.1.4] - 2026-07-11

### Added

- Documented Dual-Licensing assessment (Community-only) in ROADMAP.md.

### Fixed

- Removed em-dashes from ROADMAP.md headings.

## [0.1.3] - 2026-07-11

### Fixed

- Updated actions/checkout and actions/setup-python to their latest major versions in CI, since GitHub is deprecating the Node.js 20 runtime and older action versions were being forced onto Node 24 and crashing during post-run cleanup.

## [0.1.2] - 2026-07-10

### Fixed

- Removed em-dashes from CHANGELOG.md date headers, replaced with plain hyphens
- Changed the language-switch link from a blockquote to plain text

## [0.1.1] - 2026-07-10

### Fixed

- Removed a duplicate "New here? -> beginners guide" callout from README.md (was shown twice)

### Added

- Added the "New here?" beginner guide callout to README.de.md (was missing)

## [0.1.0] - 2026-06-15
### Added
- Initial import: FastAPI backend
- Nginx reverse proxy configuration
- Docker Compose stack
- Basic portal landing page
