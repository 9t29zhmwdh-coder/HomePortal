# Changelog

All notable changes to HomePortal will be documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.3.0] - 2026-09-24

### Added

- Settings in the browser behind the gear icon: links (add, edit, reorder, delete), page texts, appearance, access. Before this, changing anything meant editing `portal.yaml` on the server.
- Admin password, set on first start. Stored as an Argon2 hash in `auth.json` (mode 0600); sessions are signed HttpOnly, SameSite=Strict cookies; every form carries a CSRF token; five wrong passwords lock the client out for five minutes; changing the password ends every session.
- Five themes: Midnight, Glass, Sunrise, Playful, Paper.
- Backgrounds: four patterns drawn in CSS, seven bundled photos (CC0, sources in `app/static/backgrounds/CREDITS.md`), or your own upload. Uploads are re-encoded as JPEG, which removes location and camera data; JPEG, PNG, WebP and iPhone HEIC up to 20 MB.
- Five bundled fonts under the SIL Open Font License: Inter, Nunito, Fredoka, Playfair Display, JetBrains Mono.
- Interface in English and German, following the browser unless set.
- Optional: require the password to view the page, the album and uploaded images.
- Two-column tiles on phones.

### Changed

- Settings live in `portal.json` in `DATA_PATH`. An existing `portal.yaml` is imported once on first start, and its default headings are dropped so they follow the language.
- The data folder is mounted read-write, since settings and uploads are saved there.
- Nginx accepts request bodies up to 21 MB for uploads (its default of 1 MB would have refused every photo).

### Security

- Behind Nginx every request came from the same address, so the login lockout would have locked everyone out at once, and anyone on the network could have locked out the admin on purpose. Uvicorn now takes the client address from Nginx, which overwrites any `X-Forwarded-For` sent by the client. CI checks that a forged header does not get around the lockout.

---

## [1.2.0] - 2026-09-24

### Added

- The page shows your own content. Title, headings and links come from `portal.yaml` in the `DATA_PATH` folder, the album shows the images in its `photos/` subfolder. Both are read on every request, so an edit shows up on the next reload. Before this, the four links pointed at `#` and the album showed four built-in demo pictures, with no way to change either.
- A first-start notice that says where to put `portal.yaml`, instead of placeholder links that looked real.
- `/healthz` for container health checks.
- `examples/portal.yaml` and the placeholder images in `examples/photos/` as a starting point.

### Security

- Only `http://` and `https://` link URLs are rendered; a `javascript:` or `data:` URL in `portal.yaml` is skipped and reported.
- `/photos/{name}` serves a file only when that exact name is in the album list, so `../`, hidden files and non-images return 404.
- The data folder is mounted read-only.

### Fixed

- The stylesheet never loaded behind Nginx. Nginx answered `/static/` from a folder that only exists inside the app container, so every deployment through `docker compose` showed an unstyled page. The CI smoke test only checked that `/` answered and missed it; it now also fetches the stylesheet, a link and a photo through Nginx.
- Link names and descriptions ran into each other on one line.
- The install instructions said `cd home-portal`; the cloned folder is `HomePortal`.

### Removed

- `APP_SECRET_KEY`, SQLite and "sessions" from the documentation and `.env.example`. None of them was ever used.
- `python-multipart` and `aiofiles`, which nothing imported.

---

## [1.1.9] - 2026-08-04

### Fixed

- The release workflow no longer fails when the release for a tag already exists. It called `gh release create` unconditionally and aborted with `a release with the same tag name already exists` whenever the release had come about some other way. The build had succeeded by then; only the step after it went red. In repositories that attach binaries the release was left with nothing to download, which is the same failure wearing a friendlier face.

---

## [1.1.8] - 2026-08-04

### Changed

- `uvicorn[standard]` minimum raised from 0.29.0 to 0.52.0 and `python-multipart` from 0.0.9 to 0.0.32. Both are lower bounds in the requirements, so the installed versions were already newer; what changes is that an old one can no longer be resolved.

---

## [1.1.7] - 2026-07-31

### Fixed

- The supported-versions table in `SECURITY.md` still listed `0.1.x`, a release line that no longer exists. Somebody reporting a vulnerability reads that table first, and it told them the current release was out of scope. It lists `1.1.x`.

---

## [1.1.6] - 2026-07-31

### Changed

- Both READMEs now open with the situation the portal solves, which is that everyone else in the house has no idea which port a service is on, rather than describing the stack it is built from. A short paragraph says that anyone wanting live status or service health is better served by Homer, Heimdall or Dashy, because this is deliberately a page of links.

---

## [1.1.5] - 2026-07-29

### Security

- The release workflow no longer grants `contents: write` for its whole run. The permission moves to the one job that publishes the release, and everything else runs with `contents: read`. OpenSSF Scorecard scores the Token-Permissions check 0 out of 10 whenever any workflow holds a top-level write permission, regardless of how little of the run needs it, so this single line was what held the check at zero.

---

## [1.1.4] - 2026-07-29

### Added

- `.github/workflows/release.yml`. Pushing a version tag produced nothing here: the tag landed in the repository and no release was ever created, which is how several versions ended up tagged but unreleased. The gap only showed when the tag list was compared against the release list. Release notes are taken from the matching `CHANGELOG.md` section, so they are not maintained separately from the file.

---

## [1.1.3] - 2026-07-29

### Changed

Dependency and workflow updates merged since 1.1.2:

- chore(ci): bump the actions group across 1 directory with 4 updates

---

## [1.1.2] - 2026-07-28

### Changed

- CodeQL moved from GitHub's default setup to an advanced setup with a committed `.github/workflows/codeql.yml`. The default setup skips pull requests that touch no code of a given language, so a dependency pull request changing only a lock file reported `skipping` on the required `Analyze (...)` checks forever and could never be merged. The workflow runs on every pull request regardless of what changed and uses the `security-extended` query suite, which the default setup does not allow choosing. Required checks are unchanged.
- The CodeQL job requests only `security-events: write` beyond the workflow-level `contents: read`. Repeating read grants at job level is what OpenSSF Scorecard counts as excessive token permissions, and it costs the full `Token-Permissions` score.
- Dependabot now groups only minor and patch updates per ecosystem; majors arrive as individual pull requests. The previous grouping bundled breaking changes with urgently needed security patches into one unreviewable diff. Actions stay grouped wholesale. Follows `engineering-standards` v0.11.0.

## [1.1.1] - 2026-07-28

### Added

- `.github/dependabot.yml`, with grouped weekly updates. The file was missing, and without it there are no version updates at all: repository security alerts only fire for disclosed vulnerabilities, which is how action pins across this portfolio quietly went stale. Follows `engineering-standards` v0.10.0.

### Fixed

- `actions/checkout` pins now carry the full version in the comment instead of a bare major, and all workflows use the same SHA.

## [1.1.0] - 2026-07-28

### Added

- `ruff format --check` in CI, which did not exist. The tree was already formatted, so nothing changed in the source; the check simply keeps it that way from here on.

### Changed

- CI installed ruff with a bare `pip install ruff`, which resolves to whatever the newest release happens to be on the day the job runs. Now pinned to `ruff==0.16.0`. This is the case `engineering-standards` v0.7.0 describes: an unpinned formatter turns CI red on unchanged source as soon as upstream changes what counts as formatted, which is what happened to `AdapterForge` on 2026-07-28.

## [1.0.1] - 2026-07-20

### Changed

- OpenSSF Scorecard workflow and badge.
- `copilot-instructions.md` for consistent AI-assisted contributions.
- Unified the EN/DE language-switch link format.
- Coverage reporting in CI (pytest-cov).
- Split the README's security/CI badges onto their own line, separate from the platform/tech/AI badges (they were rendering as a single merged line).

## [1.0.0] - 2026-07-17

First stable release: CI now actually builds and boots the full
`docker compose up` stack described in the README and verifies the
portal responds, turning "should work" into a tested guarantee. That
real, tested, installable distribution is the prerequisite for a 1.0
release per this portfolio's own SemVer discipline.

### Added
- CI job (`docker-smoke-test`) that runs `docker compose up --build` and confirms the portal responds through nginx, verifying the documented Installation steps actually work end to end.

## [0.2.1] - 2026-07-17

### Changed
- CI: added an explicit `permissions: contents: read` block to the workflow(s) that were missing one (CodeQL `actions/missing-workflow-permissions`), narrowing the default GITHUB_TOKEN scope.

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
