<div align="center">
  <img src="RayStudio.png" alt="RayStudio Logo" width="120"/>

  <h1>Home Portal</h1>
</div>

[🇩🇪 Deutsche Version](README.de.md)

**One page on your network that links to everything you self-host, so nobody has to remember which port it was on.**

Your NAS is on `:5000`, Home Assistant on `:8123`, the media server somewhere
else. You know them. Nobody else in the house does, and neither will you after
a holiday.

Home Portal is one landing page with those links on it, plus a small photo
album, running as a Docker container on the NAS or server you already have.
You set it up in the browser: links, a theme, a background photo or your own
picture, a font, English or German.

**Not for you if** you need live status, sensor values or service health
today. Homer, Heimdall and Dashy show those; Home Portal does not yet, it is
still a page of links.

[![CI](https://github.com/9t29zhmwdh-coder/HomePortal/actions/workflows/ci.yml/badge.svg)](https://github.com/9t29zhmwdh-coder/HomePortal/actions) [![CodeQL](https://github.com/9t29zhmwdh-coder/HomePortal/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/9t29zhmwdh-coder/HomePortal/security/code-scanning) [![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/9t29zhmwdh-coder/HomePortal/badge)](https://securityscorecards.dev/viewer/?uri=github.com/9t29zhmwdh-coder/HomePortal) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13705/badge)](https://www.bestpractices.dev/projects/13705)

![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey?logo=linux&logoColor=black) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![AI | Claude Code](https://img.shields.io/badge/AI-Claude_Code-black?logo=anthropic&logoColor=white) ![AI | Copilot](https://img.shields.io/badge/AI-Copilot-black?logo=github&logoColor=white)

> **How it runs:** Home Portal is a self-hosted web app, not a desktop tool. It runs continuously as a Docker container (FastAPI behind Nginx) on your NAS or server, and you open it in any browser on your network; there is no separate installer beyond `docker compose up`.

![Home Portal](docs/screenshot.jpg)

<p align="center"><sub>Screenshot: theme "Glass" with the bundled "Alpine lake" photo, links from <a href="examples/portal.yaml">examples/portal.yaml</a>, placeholder images from <code>examples/photos/</code>.</sub></p>

---

> 🌱 New here? → [Step-by-step guide for beginners](GETTING_STARTED.md)

---

**In practice:** you deploy the container once on your NAS or home server, and every device on your network gets a single landing page with quick links to your other self-hosted services (NAS, router, media server, and similar) and a small photo album. On first start you set an admin password; after that the gear icon opens the settings, where you add links and pick how the page looks. Viewing stays open on your network unless you require the password for that too.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com) (Python 3.12) |
| Reverse Proxy | [Nginx](https://nginx.org) (Alpine) |
| Runtime | Docker & Docker Compose |
| Content | `portal.json` in the data folder, photos and uploads next to it |

## Requirements

- Docker & Docker Compose
- NAS or Linux server

## Installation

```bash
# 1. Clone repository
git clone https://github.com/9t29zhmwdh-coder/HomePortal.git
cd HomePortal

# 2. Configure environment
cp .env.example .env
nano .env

# 3. Build and start
docker compose up -d --build
```

The portal will be available at `http://YOUR-HOST`.

## Directory Structure

```
HomePortal/
├── app/
│   ├── main.py           # page, photos, login and setup routes
│   ├── settings.py       # every route that changes the portal
│   ├── store.py          # portal.json, imports an old portal.yaml once
│   ├── auth.py           # admin password (Argon2) and sessions
│   ├── uploads.py        # background uploads, re-encoded without metadata
│   ├── catalog.py        # themes, fonts, patterns and photos to choose from
│   ├── i18n.py           # English and German interface text
│   ├── templates/        # Jinja2 templates
│   └── static/           # stylesheet, fonts, background photos
├── examples/             # portal.yaml and placeholder photos to start from
├── nginx/
│   └── default.conf      # Nginx reverse proxy config
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATA_PATH` | Folder for settings, uploads and your `photos/` | `/volume1/docker/home-portal` |
| `TZ` | Timezone | `Europe/Zurich` |

## Setting it up

**First start.** Open the portal and click the gear icon. Home Portal asks for
an admin password (at least 10 characters). Whoever sets it first owns the
portal, so do this right after `docker compose up`.

**Settings.** Behind the gear icon, after logging in:

![Settings](docs/settings.jpg)

| Section | What you can change |
|---|---|
| Appearance | Theme (Midnight, Glass, Sunrise, Playful, Paper), background (none, four drawn patterns, seven bundled photos, or your own upload), font (Inter, Nunito, Fredoka, Playfair Display, JetBrains Mono), language (browser, English, German) |
| Page texts | Title, subtitle, both headings |
| Links | Add, edit, reorder, delete; name and an `http://` or `https://` address are required, description and emoji icon are optional |
| Access | Require the password to view the page too; change the password |

**Album.** Photos come from the `photos` folder in `DATA_PATH`
(`.jpg`, `.png`, `.webp`, `.gif`, up to 60, sorted by name, file name becomes
the caption). Copy them there with the NAS file manager; there is no photo
upload in the browser.

**Uploaded backgrounds** are decoded and saved again as JPEG, which removes
location and camera data. JPEG, PNG, WebP and iPhone HEIC up to 20 MB.

**Coming from 1.2?** An existing `portal.yaml` is imported once on first start
into `portal.json`. After that the settings page is the place to edit; the
YAML file is no longer read.

Everything is bundled in the container: fonts, patterns and photos load from
your server, not from the internet. Photo credits and licences (all CC0) are in
[`app/static/backgrounds/CREDITS.md`](app/static/backgrounds/CREDITS.md), font
licences (SIL OFL) in
[`app/static/fonts/LICENSE-FONTS.txt`](app/static/fonts/LICENSE-FONTS.txt).

## Useful Commands

```bash
# View logs
docker compose logs -f app

# Restart app
docker compose restart app

# Rebuild after code changes
docker compose up -d --build

# Stop
docker compose down
```

---

## Uninstall / Cleanup

```bash
docker compose down
```

Then delete the cloned repository directory. In `DATA_PATH`, Home Portal wrote `portal.json` (settings and links), `auth.json` (password hash) and `uploads/`; your `photos/` folder is yours and was only read. Delete what you no longer need. Home Portal has no other host-level state.

---

**Author:** [Rafael Yilmaz](https://github.com/9t29zhmwdh-coder) · **Status:** Active · ![version](https://img.shields.io/github/v/release/9t29zhmwdh-coder/HomePortal?color=6b7280&style=flat-square) · **License:** MIT
