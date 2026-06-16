# Architecture

## Overview

HomePortal is a lightweight self-hosted personal web portal built with FastAPI,
served behind Nginx, and orchestrated via Docker Compose.

```
homeportal/
├── app/
│   ├── main.py         # FastAPI app
│   ├── routers/        # API routes
│   └── static/         # Frontend assets
├── nginx/
│   └── default.conf    # Nginx reverse proxy config
├── docker-compose.yml  # Stack definition
└── Dockerfile          # App container
```

## Stack

| Layer    | Technology           |
|----------|----------------------|
| Backend  | Python 3.12, FastAPI |
| Server   | Nginx                |
| Runtime  | Docker Compose       |

## CI

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest
```
