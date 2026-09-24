"""Keeps everything the settings page can change in one JSON file: DATA_DIR/portal.json.

A single file stays readable and easy to back up, and one admin editing at a time
is the only writer, so a lock plus an atomic replace is all the safety it needs.
On first start an existing portal.yaml is imported, so 1.2 setups keep their links.
"""

import copy
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path

from app import portal as portal_yaml

STORE_NAME = "portal.json"
SCHEMA_VERSION = 1
_lock = threading.Lock()
LEGACY_DEFAULTS = {"links_heading": "Links", "album_heading": "Album"}

DEFAULTS = {
    "version": SCHEMA_VERSION,
    "site": {
        "title": "Home Portal",
        "subtitle": "",
        "links_heading": "",
        "album_heading": "",
    },
    "appearance": {
        "theme": "midnight",
        "background": {"kind": "none", "value": ""},
        "font": "inter",
        "language": "auto",
    },
    "access": {"require_login_to_view": False},
    "links": [],
}


def store_path(data_dir: Path) -> Path:
    return data_dir / STORE_NAME


def load(data_dir: Path) -> dict:
    path = store_path(data_dir)
    if not path.is_file():
        return first_load(data_dir)
    with path.open(encoding="utf-8") as handle:
        return merge_defaults(json.load(handle))


def first_load(data_dir: Path) -> dict:
    """Imports once and writes the result, so link ids stay the same from one request to the next."""
    state = import_from_yaml(data_dir)
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


def import_from_yaml(data_dir: Path) -> dict:
    state = copy.deepcopy(DEFAULTS)
    legacy = portal_yaml.load_portal(data_dir)
    if not legacy.config_found:
        return state
    for key in ("title", "subtitle", "links_heading", "album_heading"):
        value = getattr(legacy, key)
        # 1.2 filled in "Links" and "Album" when the file had no heading; keeping those
        # would pin the headings to English even when the page runs in German.
        if value != LEGACY_DEFAULTS.get(key):
            state["site"][key] = value
    state["links"] = [new_link(vars(link)) for link in legacy.links]
    return state


def new_link(fields: dict) -> dict:
    return {
        "id": uuid.uuid4().hex[:12],
        "name": fields.get("name", ""),
        "url": fields.get("url", ""),
        "description": fields.get("description", ""),
        "icon": fields.get("icon", ""),
    }
