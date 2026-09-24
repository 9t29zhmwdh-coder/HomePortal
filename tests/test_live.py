import json

import httpx
import pytest

from app import live

HA = "http://ha.test:8123"
TOKEN = "secret-token"
STATES = {
    "sensor.temp": {
        "state": "21.5",
        "attributes": {"friendly_name": "Living room", "unit_of_measurement": "°C"},
    },
    "light.kitchen": {"state": "on", "attributes": {"friendly_name": "Kitchen"}},
}
WEATHER = {
    "current": {"temperature_2m": 12.4, "weather_code": 3, "wind_speed_10m": 7.6},
    "daily": {"temperature_2m_max": [18.2], "temperature_2m_min": [6.9]},
}


def handler(request: httpx.Request) -> httpx.Response:
    host, path = request.url.host, request.url.path
    if host == "ha.test":
        if request.headers.get("authorization") != f"Bearer {TOKEN}":
            return httpx.Response(401)
        if path == "/api/":
            return httpx.Response(200, json={"message": "API running."})
        entity = path.removeprefix("/api/states/")
        return (
            httpx.Response(200, json=STATES[entity])
            if entity in STATES
            else httpx.Response(404)
        )
    if host == "up.test":
        return httpx.Response(401)
    if host == "broken.test":
        return httpx.Response(503)
    if host == "api.open-meteo.com":
        return httpx.Response(200, json=WEATHER)
    if host == "geocoding-api.open-meteo.com":
        results = [
            {
                "name": "Aarau",
                "country_code": "CH",
                "latitude": 47.39,
                "longitude": 8.04,
            }
        ]
        return httpx.Response(
            200,
            json={"results": results if request.url.params["name"] == "Aarau" else []},
        )
    raise httpx.ConnectError("unreachable", request=request)


@pytest.fixture(autouse=True)
def fake_network(monkeypatch):
    live.clear_cache()
    requests: list = []

    def recording(request):
        requests.append(request)
        return handler(request)

    def make_client(**options):
        options.pop("verify", None)
        return httpx.AsyncClient(transport=httpx.MockTransport(recording), **options)

    monkeypatch.setattr(live, "make_client", make_client)
    return requests


def connect(admin, token=TOKEN, url=HA):
    return admin.post(
        "/settings/connections/ha",
        data={"csrf": admin.csrf, "url": url, "token": token},
    )


def board(data_dir):
    return json.loads((data_dir / "portal.json").read_text())["dashboards"][0]


def add(admin, board_id, **fields):
    return admin.post(f"/edit/{board_id}/tiles", data={"csrf": admin.csrf, **fields})


@pytest.fixture
def board_id(admin, data_dir):
    admin.get("/")
    return board(data_dir)["id"]


def test_connecting_home_assistant_checks_the_token(admin, data_dir):
    assert "ha_unauthorized" in connect(admin, token="wrong").headers["location"]
    assert "msg=ha_ok" in connect(admin).headers["location"]
    stored = data_dir / "connections.json"
    assert stored.stat().st_mode & 0o077 == 0
    assert TOKEN not in (data_dir / "portal.json").read_text()
    assert TOKEN not in admin.get("/settings").text


def test_changed_address_needs_the_token_again(admin):
    connect(admin)
    moved = admin.post(
        "/settings/connections/ha",
        data={"csrf": admin.csrf, "url": "http://evil.test", "token": ""},
    )
    assert "ha_token_required" in moved.headers["location"]
    same = admin.post(
        "/settings/connections/ha", data={"csrf": admin.csrf, "url": HA, "token": ""}
    )
    assert "msg=ha_ok" in same.headers["location"]


def test_ha_tile_shows_values_and_missing_entities(admin, board_id):
    connect(admin)
    add(
        admin,
        board_id,
        type="ha",
        title="Wohnzimmer",
        entities="sensor.temp\nlight.kitchen, sensor.gone",
    )
    page = admin.get("/", headers={"accept-language": "de"}).text
    assert "21.5 °C" in page
    assert "Kitchen" in page and ">An<" in page
    assert "Nicht gefunden" in page


def test_ha_tile_without_connection_says_so(admin, board_id):
    add(admin, board_id, type="ha", title="x", entities="sensor.temp")
    assert "not connected yet" in admin.get("/").text


@pytest.mark.parametrize(
    "entities", ["", "not an entity", "sensor.temp/../../api", "a.b\n" * 9]
)
def test_malformed_entity_ids_are_refused(admin, data_dir, board_id, entities):
    response = add(admin, board_id, type="ha", title="x", entities=entities)
    assert "invalid_ha" in response.headers["location"]
    assert board(data_dir)["tiles"] == []


def test_many_entities_start_as_a_large_tile(admin, data_dir, board_id):
    add(admin, board_id, type="ha", title="x", entities="a.a\nb.b\nc.c\nd.d")
    tile = board(data_dir)["tiles"][0]
    assert (tile["w"], tile["h"]) == (2, 2)


def test_status_tiles_show_up_and_down(admin, board_id):
    add(admin, board_id, type="status", name="Router", url="http://up.test")
    add(admin, board_id, type="status", name="Printer", url="http://broken.test")
    add(admin, board_id, type="status", name="Gone", url="http://nowhere.test")
    page = admin.get("/").text
    assert page.count("is-up") == 1
    assert page.count("is-down") == 2


def test_status_results_are_cached(admin, board_id, fake_network):
    add(admin, board_id, type="status", name="Router", url="http://up.test")
    admin.get("/")
    admin.get("/")
    assert sum(1 for r in fake_network if r.url.host == "up.test") == 1


def test_weather_tile_geocodes_once_and_shows_the_forecast(admin, data_dir, board_id):
    add(admin, board_id, type="weather", place="Aarau")
    tile = board(data_dir)["tiles"][0]
    assert tile["config"] == {
        "place": "Aarau, CH",
        "latitude": 47.39,
        "longitude": 8.04,
    }
    page = admin.get("/", headers={"accept-language": "de"}).text
    assert "12°" in page and "Bewölkt" in page and "7° / 18°" in page


def test_unknown_place_is_refused(admin, data_dir, board_id):
    assert (
        "invalid_weather"
        in add(admin, board_id, type="weather", place="Nirgendwo").headers["location"]
    )
    assert board(data_dir)["tiles"] == []


def test_clock_accepts_only_real_time_zones(admin, data_dir, board_id):
    assert (
        "invalid_clock"
        in add(admin, board_id, type="clock", timezone="Mars/Olympus").headers[
            "location"
        ]
    )
    add(admin, board_id, type="clock", title="Zürich", timezone="Europe/Zurich")
    assert 'data-timezone="Europe/Zurich"' in admin.get("/").text


def test_live_fragment_refreshes_one_tile(admin, data_dir, board_id):
    connect(admin)
    add(admin, board_id, type="ha", title="x", entities="sensor.temp")
    tile_id = board(data_dir)["tiles"][0]["id"]
    fragment = admin.get(f"/live/{board_id}/{tile_id}").text
    assert "21.5" in fragment and "<html" not in fragment
    assert admin.get(f"/live/{board_id}/nothing").status_code == 404


def test_live_fragment_respects_login_to_view(admin, data_dir, board_id):
    from fastapi.testclient import TestClient

    from app.main import app

    add(admin, board_id, type="status", name="Router", url="http://up.test")
    tile_id = board(data_dir)["tiles"][0]["id"]
    admin.post("/settings/access", data={"csrf": admin.csrf, "require_login": "on"})
    stranger = TestClient(app, follow_redirects=False)
    assert stranger.get(f"/live/{board_id}/{tile_id}").headers["location"] == "/login"


def test_disconnect_forgets_the_token(admin, data_dir):
    connect(admin)
    admin.post("/settings/connections/ha/forget", data={"csrf": admin.csrf})
    assert TOKEN not in (data_dir / "connections.json").read_text()
