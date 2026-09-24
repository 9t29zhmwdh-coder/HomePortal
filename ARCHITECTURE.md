# Architecture

## Overview

HomePortal renders one page from two things in a data folder: `portal.yaml`
(title, headings, links) and `photos/` (the album). FastAPI reads both on every
request, Nginx sits in front, Docker Compose runs the two containers.

```
HomePortal/
├── app/
│   ├── main.py            # routes: /, /photos/{name}, /healthz
│   ├── portal.py          # reads and validates portal.yaml, lists photos/
│   ├── templates/         # index.html (Jinja2, autoescaped)
│   └── static/css/        # stylesheet
├── examples/
│   ├── portal.yaml        # starting point for your own portal.yaml
│   └── photos/            # four placeholder images, used for tests and screenshots
├── nginx/default.conf     # reverse proxy, forwards everything to the app
├── tests/test_smoke.py
├── docker-compose.yml     # mounts DATA_PATH read-only at /data
└── Dockerfile
```

## Data flow

1. `GET /` calls `load_portal()`, which reads `/data/portal.yaml` and lists `/data/photos/`.
2. Links whose URL is not `http(s)://host` are dropped and reported on the page, so a
   `javascript:` or `data:` URL can never become a clickable link.
3. `GET /photos/{name}` serves a file only if that exact name is in the photo list,
   which rules out `../`, hidden files and anything that is not an image.

There is no database and no write path: the container mounts the data folder read-only.

## Stack

| Layer    | Technology                     |
|----------|--------------------------------|
| Backend  | Python 3.12, FastAPI, PyYAML   |
| Proxy    | Nginx (Alpine)                 |
| Runtime  | Docker Compose                 |

## CI

`.github/workflows/ci.yml` runs ruff (lint and format), the pytest suite with
coverage, and a Docker Compose smoke test that starts the real stack with the
example data and checks through Nginx that a link, a photo and the stylesheet
are served.
