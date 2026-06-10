> 🇩🇪 [Deutsche Version](README.de.md)

# Home Portal

A lightweight, self-hosted personal web portal built with FastAPI and Docker. Designed to run on a NAS or any Linux server.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com) (Python 3.12) |
| Reverse Proxy | [Nginx](https://nginx.org) (Alpine) |
| Runtime | Docker & Docker Compose |
| Storage | SQLite + local file system |

## Requirements

- Docker & Docker Compose
- NAS or Linux server

## Installation

```bash
# 1. Clone repository
git clone https://github.com/9t29zhmwdh-coder/home-portal.git
cd home-portal

# 2. Configure environment
cp .env.example .env
nano .env

# 3. Build and start
docker compose up -d --build
```

The portal will be available at `http://YOUR-HOST`.

## Directory Structure

```
home-portal/
├── app/
│   └── main.py          # FastAPI application entry point
├── nginx/
│   └── default.conf     # Nginx reverse proxy config
├── static/              # Static assets (CSS, JS, images)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATA_PATH` | Path for persistent data | `/volume1/docker/home-portal` |
| `TZ` | Timezone | `Europe/Zurich` |
| `APP_SECRET_KEY` | Secret key for sessions | `random-string` |

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

**Author:** [Rafael Yilmaz](https://github.com/9t29zhmwdh-coder) &nbsp;·&nbsp; **Status:** Production Ready &nbsp;·&nbsp; **Last Updated:** June 2026
