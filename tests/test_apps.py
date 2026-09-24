import json

import httpx
import pytest

from app import live

APPS = {
    "/open": {},
    "/deny": {"X-Frame-Options": "DENY"},
    "/sameorigin": {"X-Frame-Options": "sameorigin"},
    "/csp-self": {
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'self'"
    },
    "/csp-portal": {"Content-Security-Policy": "frame-ancestors http://testserver"},
    "/csp-any": {"Content-Security-Policy": "frame-ancestors *"},
}


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.host != "apps.test":
        raise httpx.ConnectError("unreachable", request=request)
    return httpx.Response(200, headers=APPS[request.url.path], text="<h1>app</h1>")


@pytest.fixture(autouse=True)
def fake_network(monkeypatch):
    live.clear_cache()

    def make_client(**options):
        options.pop("verify", None)
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), **options)

    monkeypatch.setattr(live, "make_client", make_client)


@pytest.fixture
def board_id(admin, data_dir):
    admin.get("/")
    return json.loads((data_dir / "portal.json").read_text())["dashboards"][0]["id"]


def add_app(admin, board_id, path):
    return admin.post(
        f"/edit/{board_id}/tiles",
        data={
            "csrf": admin.csrf,
            "type": "app",
            "name": "App",
            "url": f"http://apps.test{path}",
        },
    )


@pytest.mark.parametrize(
    "path, framed",
    [
        ("/open", True),
        ("/deny", False),
        ("/sameorigin", False),
        ("/csp-self", False),
        ("/csp-portal", True),
        ("/csp-any", True),
    ],
)
def test_app_tile_frames_only_what_allows_it(admin, board_id, path, framed):
    add_app(admin, board_id, path)
    page = admin.get("/").text
    assert ('<iframe src="http://apps.test' in page) is framed
    assert "Open in a new tab" in page


def test_unreachable_app_is_explained(admin, board_id):
    admin.post(
        f"/edit/{board_id}/tiles",
        data={
            "csrf": admin.csrf,
            "type": "app",
            "name": "Old",
            "url": "http://gone.test/",
        },
    )
    assert "does not answer" in admin.get("/").text


def test_app_tile_needs_a_safe_url(admin, board_id):
    response = admin.post(
        f"/edit/{board_id}/tiles",
        data={
            "csrf": admin.csrf,
            "type": "app",
            "name": "x",
            "url": "javascript:alert(1)",
        },
    )
    assert "invalid_app" in response.headers["location"]


def test_app_tab_fills_the_page(admin, data_dir):
    admin.get("/")
    admin.post(
        "/settings/dashboards",
        data={"csrf": admin.csrf, "name": "Media", "app_url": "http://apps.test/open"},
    )
    tab = json.loads((data_dir / "portal.json").read_text())["dashboards"][1]
    assert tab["app_url"] == "http://apps.test/open"
    page = admin.get(f"/d/{tab['id']}").text
    assert 'class="app-tab"' in page and '<iframe src="http://apps.test/open"' in page
    assert f'href="/edit/{tab["id"]}"' not in page


def test_app_tab_url_must_be_safe(admin, data_dir):
    admin.get("/")
    response = admin.post(
        "/settings/dashboards",
        data={"csrf": admin.csrf, "name": "X", "app_url": "data:text/html,x"},
    )
    assert "invalid_app_url" in response.headers["location"]
    assert len(json.loads((data_dir / "portal.json").read_text())["dashboards"]) == 1


def test_portal_cannot_be_framed_by_other_sites(client):
    headers = client.get("/").headers
    assert headers["x-frame-options"] == "SAMEORIGIN"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "same-origin"


def test_frame_ancestor_parsing():
    assert live.frame_ancestors("default-src 'self'") is None
    assert live.frame_ancestors("frame-ancestors 'none'") == ["'none'"]
    assert live.frame_refusal("", "frame-ancestors 'none'") == "embed_refused_csp"
