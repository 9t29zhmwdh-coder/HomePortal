> 🇬🇧 [English Version](README.md)

# Home Portal

Ein schlankes, selbst gehostetes persönliches Webportal auf Basis von FastAPI und Docker. Läuft auf einem NAS oder beliebigem Linux-Server.

## Tech Stack

| Komponente | Technologie |
|-----------|-----------|
| Backend | [FastAPI](https://fastapi.tiangolo.com) (Python 3.12) |
| Reverse Proxy | [Nginx](https://nginx.org) (Alpine) |
| Laufzeitumgebung | Docker & Docker Compose |
| Speicher | SQLite + lokales Dateisystem |

## Voraussetzungen

- Docker & Docker Compose
- NAS oder Linux-Server

## Installation

```bash
# 1. Repo klonen
git clone https://github.com/9t29zhmwdh-coder/home-portal.git
cd home-portal

# 2. Konfiguration anpassen
cp .env.example .env
nano .env

# 3. Bauen und starten
docker compose up -d --build
```

Das Portal ist danach unter `http://DEIN-HOST` erreichbar.

## Verzeichnisstruktur

```
home-portal/
├── app/
│   └── main.py          # FastAPI Einstiegspunkt
├── nginx/
│   └── default.conf     # Nginx Reverse-Proxy-Konfiguration
├── static/              # Statische Dateien (CSS, JS, Bilder)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Konfiguration

`.env.example` nach `.env` kopieren und anpassen:

| Variable | Beschreibung | Beispiel |
|----------|-------------|---------|
| `DATA_PATH` | Pfad für persistente Daten | `/volume1/docker/home-portal` |
| `TZ` | Zeitzone | `Europe/Zurich` |
| `APP_SECRET_KEY` | Secret Key für Sessions | `zufaelliger-string` |

## Nützliche Befehle

```bash
# Logs anzeigen
docker compose logs -f app

# App neustarten
docker compose restart app

# Nach Code-Änderungen neu bauen
docker compose up -d --build

# Stoppen
docker compose down
```

---

**Author:** [Rafael Yilmaz](https://github.com/9t29zhmwdh-coder) &nbsp;·&nbsp; **Status:** Production Ready &nbsp;·&nbsp; **Last Updated:** June 2026
