"""Keeps everything the settings can change in one JSON file: DATA_DIR/portal.json.

A single file stays readable and easy to back up, and one admin editing at a time
is the only writer, so a lock plus an atomic replace is all the safety it needs.

Schema history: 1.2 read portal.yaml, 1.3 wrote schema 1 (a flat link list),
1.4 writes schema 2 (tabs with tiles). Older data is migrated on first load.
"""

import copy
import json
import os
import tempfile
import threading
from pathlib import Path

from app import portal as portal_yaml
from app import tiles

STORE_NAME = "portal.json"
SCHEMA_VERSION = 2
_lock = threading.Lock()
LEGACY_DEFAULTS = {"links_heading": "Links", "album_heading": "Album"}

DEFAULTS = {
    "version": SCHEMA_VERSION,
    "site": {"title": "Home Portal", "subtitle": ""},
    "appearance": {
        # A new install should look like a dashboard from the first second; saved
        # appearances of existing installs are kept as they are.
        "theme": "glass",
        "background": {"kind": "photo", "value": "alpine-lake"},
        "font": "inter",
        "language": "auto",
    },
    "access": {"require_login_to_view": False},
    "dashboards": [],
}


def store_path(data_dir: Path) -> Path:
    return data_dir / STORE_NAME


def load(data_dir: Path) -> dict:
    path = store_path(data_dir)
    if not path.is_file():
        return persist_quietly(data_dir, migrate(import_from_yaml(data_dir), data_dir))
    with path.open(encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("version", 1) < SCHEMA_VERSION:
        return persist_quietly(data_dir, migrate(state, data_dir))
    return merge_defaults(state)


def persist_quietly(data_dir: Path, state: dict) -> dict:
    """Writes a migrated state right away, so ids stay the same from one request to the next."""
    try:
        save(data_dir, state)
    except OSError:
        pass  # read-only data folder: the page still renders, the settings cannot save
    return state


def save(data_dir: Path, state: dict) -> None:
    with _lock:
        fd, tmp_name = tempfile.mkstemp(dir=data_dir, prefix=".portal-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_name, store_path(data_dir))


def update(data_dir: Path, change) -> dict:
    """Load, apply change(state) and save in one step."""
    state = load(data_dir)
    change(state)
    save(data_dir, state)
    return state


def merge_defaults(state: dict) -> dict:
    merged = copy.deepcopy(DEFAULTS)
    for key, value in state.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def migrate(state: dict, data_dir: Path) -> dict:
    """Turns schema 1 (flat links, one album) into schema 2 (one tab holding them as tiles)."""
    site = state.get("site", {})
    has_photos = bool(portal_yaml.list_photos(data_dir))
    board_tiles = tiles.tiles_from_links(state.get("links", []), add_album=has_photos)
    for tile in board_tiles:
        if tile["type"] == "album":
            tile["config"]["title"] = site.get("album_heading", "")
    dashboard = new_dashboard(site.get("links_heading", ""))
    dashboard["tiles"] = board_tiles
    migrated = merge_defaults(
        {k: v for k, v in state.items() if k not in ("links", "site")}
    )
    migrated["site"] = {
        "title": site.get("title", "Home Portal"),
        "subtitle": site.get("subtitle", ""),
    }
    migrated["dashboards"] = [dashboard]
    migrated["version"] = SCHEMA_VERSION
    return migrated


def new_dashboard(name: str) -> dict:
    return {"id": tiles.new_id(), "name": name, "tiles": []}


def import_from_yaml(data_dir: Path) -> dict:
    """Reads a 1.2 portal.yaml into schema 1, which migrate() then lifts to schema 2."""
    state: dict = {"version": 1, "site": {}, "links": []}
    legacy = portal_yaml.load_portal(data_dir)
    if not legacy.config_found:
        return state
    for key in ("title", "subtitle", "links_heading", "album_heading"):
        value = getattr(legacy, key)
        # 1.2 filled in "Links" and "Album" when the file had no heading; keeping those
        # would pin the headings to English even when the page runs in German.
        if value != LEGACY_DEFAULTS.get(key):
            state["site"][key] = value
    state["links"] = [vars(link) for link in legacy.links]
    return state


def find_dashboard(state: dict, dashboard_id: str | None) -> dict | None:
    boards = state["dashboards"]
    if dashboard_id is None:
        return boards[0] if boards else None
    return next((board for board in boards if board["id"] == dashboard_id), None)


def find_tile(dashboard: dict, tile_id: str) -> dict | None:
    return next((tile for tile in dashboard["tiles"] if tile["id"] == tile_id), None)
