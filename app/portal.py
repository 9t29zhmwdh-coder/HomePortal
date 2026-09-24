"""Reads the portal page from the data directory: links from portal.yaml, photos from photos/.

Both are read on every request, so an edited file shows up on the next reload
without restarting the container.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("PORTAL_DATA_DIR", "/data"))
CONFIG_NAME = "portal.yaml"
PHOTOS_NAME = "photos"
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_PHOTOS = 60
# A link is rendered as an href; anything but http(s) could be javascript: or data:.
ALLOWED_SCHEMES = {"http", "https"}


@dataclass
class Link:
    name: str
    url: str
    description: str = ""
    icon: str = ""


@dataclass
class Portal:
    title: str = "Home Portal"
    subtitle: str = ""
    links_heading: str = "Links"
    album_heading: str = "Album"
    links: list[Link] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)
    config_found: bool = False
    problems: list[str] = field(default_factory=list)


def load_portal(data_dir: Path = DATA_DIR) -> Portal:
    portal = Portal(photos=list_photos(data_dir))
    config_path = data_dir / CONFIG_NAME
    if not config_path.is_file():
        return portal
    portal.config_found = True
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as error:
        logger.warning("cannot read %s: %s", config_path, error)
        portal.problems.append(f"{CONFIG_NAME} could not be read: {error}")
        return portal
    apply_config(portal, raw)
    return portal


def apply_config(portal: Portal, raw: object) -> None:
    if not isinstance(raw, dict):
        portal.problems.append(f"{CONFIG_NAME} must be a mapping at the top level")
        return
    for key in ("title", "subtitle", "links_heading", "album_heading"):
        if isinstance(raw.get(key), str):
            setattr(portal, key, raw[key])
    for index, entry in enumerate(raw.get("links") or [], start=1):
        link = parse_link(entry)
        if link is None:
            portal.problems.append(
                f"link {index} skipped: needs a name and an http(s) url"
            )
        else:
            portal.links.append(link)


def parse_link(entry: object) -> Link | None:
    if not isinstance(entry, dict):
        return None
    name, url = entry.get("name"), entry.get("url")
    if not isinstance(name, str) or not isinstance(url, str) or not is_safe_url(url):
        return None
    return Link(
        name=name,
        url=url,
        description=str(entry.get("description") or ""),
        icon=str(entry.get("icon") or ""),
    )


def is_safe_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme.lower() in ALLOWED_SCHEMES and bool(parsed.netloc)


def photo_files(data_dir: Path = DATA_DIR) -> list[Path]:
    photos_dir = data_dir / PHOTOS_NAME
    if not photos_dir.is_dir():
        return []
    files = sorted(
        (
            entry
            for entry in photos_dir.iterdir()
            if entry.is_file()
            and entry.suffix.lower() in PHOTO_SUFFIXES
            and not entry.name.startswith(".")
        ),
        key=lambda entry: entry.name,
    )
    return files[:MAX_PHOTOS]


def list_photos(data_dir: Path = DATA_DIR) -> list[str]:
    return [entry.name for entry in photo_files(data_dir)]


def resolve_photo(name: str, data_dir: Path = DATA_DIR) -> Path | None:
    """Returns the listed file itself, so the request never builds a path: ../ and hidden files cannot match."""
    return next((entry for entry in photo_files(data_dir) if entry.name == name), None)


def caption_for(name: str) -> str:
    words = Path(name).stem.replace("_", " ").replace("-", " ")
    return words[:1].upper() + words[1:]
