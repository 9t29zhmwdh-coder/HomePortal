"""Values for live tiles: Home Assistant entities, service reachability, weather.

Every source gets a short timeout and a small cache, and all tiles of a tab are
fetched at the same time, so one slow service cannot hold up the whole page.
"""

import asyncio
import re
import time
from pathlib import Path

import httpx

from app import connections

TIMEOUT_SECONDS = 3.0
CACHE_SECONDS = {"ha": 10, "status": 20, "weather": 900, "embed": 600}
ENTITY_ID = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
MAX_ENTITIES = 8
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

_cache: dict[tuple, tuple[float, dict]] = {}
FETCHED_TYPES = ("ha", "status", "weather", "app")


def make_client(**options) -> httpx.AsyncClient:
    """Replaced in tests with a client that talks to a stand-in server."""
    return httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=False, **options)


def clear_cache() -> None:
    _cache.clear()


async def cached(key: tuple, seconds: int, fetch) -> dict:
    hit = _cache.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    value = await fetch()
    _cache[key] = (time.monotonic() + seconds, value)
    return value


async def board_data(board: dict, data_dir: Path, origin: str = "") -> dict:
    live = [tile for tile in board["tiles"] if tile["type"] in FETCHED_TYPES]
    results = await asyncio.gather(
        *(tile_data(tile, data_dir, origin) for tile in live)
    )
    return {tile["id"]: result for tile, result in zip(live, results)}


async def tile_data(tile: dict, data_dir: Path, origin: str = "") -> dict:
    config = tile["config"]
    if tile["type"] == "ha":
        return await ha_entities(data_dir, config.get("entities", []))
    if tile["type"] == "status":
        return await cached(
            ("status", config["url"]),
            CACHE_SECONDS["status"],
            lambda: probe(config["url"]),
        )
    if tile["type"] == "weather":
        key = ("weather", config["latitude"], config["longitude"])
        return await cached(
            key,
            CACHE_SECONDS["weather"],
            lambda: weather(config["latitude"], config["longitude"]),
        )
    if tile["type"] == "app":
        return await embed_status(config["url"], origin)
    return {}


async def embed_status(url: str, origin: str = "") -> dict:
    return await cached(
        ("embed", url, origin), CACHE_SECONDS["embed"], lambda: embed_check(url, origin)
    )


async def embed_check(url: str, origin: str = "") -> dict:
    """Asks the app whether a page from another origin may show it in a frame.

    The browser enforces X-Frame-Options and CSP frame-ancestors; reading the same
    headers here lets the tile explain a refusal instead of showing an empty box.
    """
    try:
        async with make_client(verify=False) as client:
            async with client.stream("GET", url) as response:
                headers = response.headers
    except httpx.HTTPError:
        return {"embeddable": False, "reason": "embed_unreachable"}
    reason = frame_refusal(
        headers.get("x-frame-options", ""),
        headers.get("content-security-policy", ""),
        origin,
    )
    return {"embeddable": reason is None, "reason": reason}


def frame_refusal(x_frame_options: str, csp: str, origin: str = "") -> str | None:
    # Home Portal always runs on another origin than the app, so SAMEORIGIN refuses it too.
    if x_frame_options.strip().upper() in ("DENY", "SAMEORIGIN"):
        return "embed_refused_xfo"
    ancestors = frame_ancestors(csp)
    if (
        ancestors is not None
        and "*" not in ancestors
        and origin.rstrip("/") not in ancestors
    ):
        return "embed_refused_csp"
    return None


def frame_ancestors(csp: str) -> list[str] | None:
    for directive in csp.split(";"):
        parts = directive.split()
        if parts and parts[0].lower() == "frame-ancestors":
            return parts[1:]
    return None


def parse_entities(text: str) -> list[str] | None:
    """One entity id per line or comma separated; None if any of them is malformed."""
    ids = [part.strip() for part in re.split(r"[\n,]+", text) if part.strip()]
    if not ids or len(ids) > MAX_ENTITIES or not all(ENTITY_ID.match(i) for i in ids):
        return None
    return ids


async def ha_entities(data_dir: Path, entity_ids: list[str]) -> dict:
    ha = connections.home_assistant(data_dir)
    if ha is None:
        return {"error": "ha_not_connected"}
    key = ("ha", ha["url"], tuple(entity_ids))
    return await cached(
        key, CACHE_SECONDS["ha"], lambda: fetch_entities(ha, entity_ids)
    )


async def fetch_entities(ha: dict, entity_ids: list[str]) -> dict:
    headers = {"Authorization": f"Bearer {ha['token']}"}
    try:
        async with make_client(headers=headers) as client:
            responses = await asyncio.gather(
                *(client.get(f"{ha['url']}/api/states/{e}") for e in entity_ids)
            )
    except httpx.HTTPError:
        return {"error": "ha_unreachable"}
    if any(r.status_code == 401 for r in responses):
        return {"error": "ha_unauthorized"}
    return {"entities": [entity_view(e, r) for e, r in zip(entity_ids, responses)]}


def entity_view(entity_id: str, response: httpx.Response) -> dict:
    if response.status_code != 200:
        return {"id": entity_id, "name": entity_id, "state": None, "unit": ""}
    body = response.json()
    attributes = body.get("attributes", {})
    return {
        "id": entity_id,
        "name": attributes.get("friendly_name") or entity_id,
        "state": body.get("state"),
        "unit": attributes.get("unit_of_measurement", ""),
    }


async def check_home_assistant(url: str, token: str) -> str:
    """Returns an i18n key: ha_ok, ha_unauthorized or ha_unreachable."""
    try:
        async with make_client(headers={"Authorization": f"Bearer {token}"}) as client:
            response = await client.get(f"{url}/api/")
    except httpx.HTTPError:
        return "ha_unreachable"
    if response.status_code == 401:
        return "ha_unauthorized"
    return "ha_ok" if response.status_code == 200 else "ha_unreachable"


async def probe(url: str) -> dict:
    """Reachability only, nothing is read: any answer below 500 counts as up.

    Certificates are not checked here, because home services often run on
    self-signed ones and the question is only whether something answers.
    """
    started = time.monotonic()
    try:
        async with make_client(verify=False) as client:
            # Streaming stops after the headers; a large start page is never downloaded.
            async with client.stream("GET", url) as response:
                status = response.status_code
    except httpx.HTTPError:
        return {"up": False}
    elapsed = round((time.monotonic() - started) * 1000)
    return {"up": status < 500, "ms": elapsed}


async def weather(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 1,
    }
    try:
        async with make_client() as client:
            body = (await client.get(WEATHER_URL, params=params)).json()
        return weather_view(body)
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return {"error": "weather_unavailable"}


def weather_view(body: dict) -> dict:
    current, daily = body["current"], body["daily"]
    return {
        "temperature": round(current["temperature_2m"]),
        "code": int(current["weather_code"]),
        "wind": round(current["wind_speed_10m"]),
        "high": round(daily["temperature_2m_max"][0]),
        "low": round(daily["temperature_2m_min"][0]),
    }


async def geocode(place: str, language: str) -> dict | None:
    params = {"name": place, "count": 1, "language": language, "format": "json"}
    try:
        async with make_client() as client:
            results = (await client.get(GEOCODE_URL, params=params)).json().get(
                "results"
            ) or []
    except (httpx.HTTPError, ValueError):
        return None
    if not results:
        return None
    hit = results[0]
    label = ", ".join(
        part for part in (hit.get("name"), hit.get("country_code")) if part
    )
    return {"place": label, "latitude": hit["latitude"], "longitude": hit["longitude"]}


# WMO weather interpretation codes, grouped: (emoji, i18n key)
WEATHER_CODES = [
    ((0,), "☀️", "wx_clear"),
    ((1, 2), "🌤️", "wx_partly"),
    ((3,), "☁️", "wx_cloudy"),
    ((45, 48), "🌫️", "wx_fog"),
    ((51, 53, 55, 56, 57), "🌦️", "wx_drizzle"),
    ((61, 63, 65, 66, 67, 80, 81, 82), "🌧️", "wx_rain"),
    ((71, 73, 75, 77, 85, 86), "🌨️", "wx_snow"),
    ((95, 96, 99), "⛈️", "wx_storm"),
]


def weather_symbol(code: int) -> tuple[str, str]:
    return next(
        ((emoji, key) for codes, emoji, key in WEATHER_CODES if code in codes),
        ("🌡️", "wx_unknown"),
    )
