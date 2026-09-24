"""Dashboards (tabs) and the tiles on them: types, allowed sizes, layout checks.

The grid has six columns. Tiles only come in fixed sizes per type, the way a page
builder offers predefined blocks, so the page stays tidy whatever gets dragged where.
"""

import uuid

COLUMNS = 6
MAX_ROWS = 60
MAX_DASHBOARDS = 12
MAX_TILES = 80

SIZES = {
    "small": (1, 1),
    "wide": (2, 1),
    "tall": (1, 2),
    "large": (2, 2),
    "banner": (4, 1),
    "full": (6, 1),
    "block": (4, 2),
    "full-2": (6, 2),
    "full-3": (6, 3),
    "block-3": (4, 3),
    "full-4": (6, 4),
}

TYPES = {
    "link": {"sizes": ("small", "wide", "tall", "large"), "default": "small"},
    "note": {
        "sizes": ("small", "wide", "tall", "large", "banner", "full"),
        "default": "wide",
    },
    "album": {"sizes": ("large", "block", "full-2", "full-3"), "default": "full-2"},
    "ha": {"sizes": ("small", "wide", "tall", "large", "banner"), "default": "wide"},
    "status": {"sizes": ("small", "wide"), "default": "small"},
    "clock": {"sizes": ("small", "wide", "large"), "default": "wide"},
    "weather": {"sizes": ("small", "wide", "large"), "default": "wide"},
    "app": {
        "sizes": ("large", "block", "block-3", "full-2", "full-3", "full-4"),
        "default": "block-3",
    },
}

LIVE_TYPES = ("ha", "status", "weather", "clock")
# Checked when the page renders, but never refreshed by live.js: that would reload the app.
EMBED_TYPES = ("app",)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def is_allowed_size(tile_type: str, w: int, h: int) -> bool:
    return any(SIZES[name] == (w, h) for name in TYPES[tile_type]["sizes"])


def new_tile(tile_type: str, config: dict, tiles: list) -> dict:
    w, h = SIZES[default_size(tile_type, config)]
    x, y = free_spot(tiles, w, h)
    return {
        "id": new_id(),
        "type": tile_type,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "config": config,
    }


def default_size(tile_type: str, config: dict) -> str:
    # More than three Home Assistant values do not fit a one-row tile.
    if tile_type == "ha" and len(config.get("entities", [])) > 3:
        return "large"
    return TYPES[tile_type]["default"]


def free_spot(tiles: list, w: int, h: int) -> tuple[int, int]:
    """First place, row by row, where a w by h tile fits without overlapping anything."""
    taken = occupied(tiles)
    for y in range(MAX_ROWS):
        for x in range(COLUMNS - w + 1):
            cells = {(x + dx, y + dy) for dx in range(w) for dy in range(h)}
            if not cells & taken:
                return x, y
    return 0, bottom(tiles)


def occupied(tiles: list) -> set:
    return {
        (t["x"] + dx, t["y"] + dy)
        for t in tiles
        for dx in range(t["w"])
        for dy in range(t["h"])
    }


def bottom(tiles: list) -> int:
    return max((t["y"] + t["h"] for t in tiles), default=0)


def layout_problem(tiles: list, layout: list) -> str | None:
    """Checks a layout sent by the editor: every tile once, allowed size, inside the grid, no overlap."""
    by_id = {t["id"]: t for t in tiles}
    if sorted(item.get("id", "") for item in layout) != sorted(by_id):
        return "layout_tiles_mismatch"
    cells: set = set()
    for item in layout:
        problem = item_problem(by_id[item["id"]], item, cells)
        if problem:
            return problem
    return None


def item_problem(tile: dict, item: dict, cells: set) -> str | None:
    try:
        x, y, w, h = (int(item[key]) for key in ("x", "y", "w", "h"))
    except (KeyError, TypeError, ValueError):
        return "layout_invalid"
    if not is_allowed_size(tile["type"], w, h):
        return "layout_bad_size"
    if x < 0 or y < 0 or x + w > COLUMNS or y + h > MAX_ROWS:
        return "layout_outside"
    mine = {(x + dx, y + dy) for dx in range(w) for dy in range(h)}
    if mine & cells:
        return "layout_overlap"
    cells |= mine
    return None


def apply_layout(tiles: list, layout: list) -> None:
    by_id = {item["id"]: item for item in layout}
    for tile in tiles:
        item = by_id[tile["id"]]
        tile.update(
            x=int(item["x"]), y=int(item["y"]), w=int(item["w"]), h=int(item["h"])
        )


def tiles_from_links(links: list, add_album: bool) -> list:
    """Schema 1 had a flat link list and one album; they become tiles on the first tab."""
    tiles: list = []
    for link in links:
        config = {
            key: link.get(key, "") for key in ("name", "url", "description", "icon")
        }
        tiles.append(new_tile("link", config, tiles))
    if add_album:
        tiles.append(new_tile("album", {"title": ""}, tiles))
    return tiles
