"""Credentials for live tiles, kept apart from portal.json in DATA_DIR/connections.json (mode 0600).

portal.json is the file people back up, copy and share; a Home Assistant token
does not belong in it. The token is never sent back to the browser, the settings
page only shows whether one is stored.
"""

import json
import os
from pathlib import Path

from app import portal as portal_data

CONNECTIONS_NAME = "connections.json"


def path_for(data_dir: Path) -> Path:
    return data_dir / CONNECTIONS_NAME


def load(data_dir: Path) -> dict:
    path = path_for(data_dir)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save(data_dir: Path, connections: dict) -> None:
    fd = os.open(path_for(data_dir), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(connections, handle)


def home_assistant(data_dir: Path) -> dict | None:
    ha = load(data_dir).get("home_assistant") or {}
    if ha.get("url") and ha.get("token"):
        return ha
    return None


def set_home_assistant(data_dir: Path, url: str, token: str) -> str | None:
    """Stores the connection; returns an i18n error key or None.

    An empty token keeps the stored one, so the form never has to show it, but
    only for the same address: otherwise a changed URL would carry the stored
    token to whatever server it now points at.
    """
    url = url.strip().rstrip("/")
    if not portal_data.is_safe_url(url):
        return "ha_invalid"
    connections = load(data_dir)
    current = connections.get("home_assistant") or {}
    token = token.strip()
    if not token and current.get("url") != url:
        return "ha_token_required"
    connections["home_assistant"] = {"url": url, "token": token or current["token"]}
    save(data_dir, connections)
    return None


def forget_home_assistant(data_dir: Path) -> None:
    connections = load(data_dir)
    connections.pop("home_assistant", None)
    save(data_dir, connections)
