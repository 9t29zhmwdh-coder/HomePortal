# Changelog

All notable changes to HomePortal will be documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
