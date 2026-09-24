import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


def board(data_dir) -> dict:
    return json.loads((data_dir / "portal.json").read_text())["dashboards"][0]


def add(admin, board_id, **fields):
    return admin.post(f"/edit/{board_id}/tiles", data={"csrf": admin.csrf, **fields})


@pytest.fixture
def board_id(admin, data_dir):
    admin.get("/")
    return board(data_dir)["id"]


def test_edit_page_needs_login(client, board_id):
    stranger = TestClient(app, follow_redirects=False)
    assert stranger.get(f"/edit/{board_id}").headers["location"] == "/login"


def test_tiles_are_added_at_the_first_free_spot(admin, data_dir, board_id):
    add(admin, board_id, type="link", name="NAS", url="http://nas.lan")
    add(admin, board_id, type="note", title="WLAN", text="Gast")
    add(admin, board_id, type="album", title="Ferien")
    tiles = board(data_dir)["tiles"]
    assert [(t["type"], t["x"], t["y"], t["w"], t["h"]) for t in tiles] == [
        ("link", 0, 0, 1, 1),
        ("note", 1, 0, 2, 1),
        ("album", 0, 1, 6, 2),
    ]


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "data:text/html,x", "keine url"]
)
def test_link_tiles_need_a_safe_url(admin, data_dir, board_id, url):
    response = add(admin, board_id, type="link", name="Bad", url=url)
    assert "invalid_link" in response.headers["location"]
    assert board(data_dir)["tiles"] == []


def test_unknown_tile_types_are_refused(admin, data_dir, board_id):
    add(admin, board_id, type="script", name="x")
    assert board(data_dir)["tiles"] == []
    assert admin.get(f"/edit/{board_id}/tiles/new?type=script").status_code == 404


def test_tile_can_be_edited_and_deleted(admin, data_dir, board_id):
    add(admin, board_id, type="note", title="Alt", text="x")
    tile_id = board(data_dir)["tiles"][0]["id"]
    admin.post(
        f"/edit/{board_id}/tiles/{tile_id}",
        data={"csrf": admin.csrf, "title": "Neu", "text": "Zeile 1\nZeile 2"},
    )
    assert board(data_dir)["tiles"][0]["config"] == {
        "title": "Neu",
        "text": "Zeile 1\nZeile 2",
    }
    assert "Zeile 1<br>Zeile 2" in admin.get("/").text
    admin.post(f"/edit/{board_id}/tiles/{tile_id}/delete", data={"csrf": admin.csrf})
    assert board(data_dir)["tiles"] == []


def test_note_text_is_escaped(admin, board_id):
    add(admin, board_id, type="note", title="t", text="<script>alert(1)</script>")
    body = admin.get("/").text
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def post_layout(admin, board_id, layout, csrf=None):
    headers = {"X-CSRF-Token": admin.csrf if csrf is None else csrf}
    return admin.post(f"/edit/{board_id}/layout", json=layout, headers=headers)


def test_layout_is_saved(admin, data_dir, board_id):
    add(admin, board_id, type="link", name="A", url="http://a.lan")
    add(admin, board_id, type="link", name="B", url="http://b.lan")
    a, b = board(data_dir)["tiles"]
    layout = [
        {"id": a["id"], "x": 4, "y": 0, "w": 2, "h": 2},
        {"id": b["id"], "x": 0, "y": 3, "w": 1, "h": 1},
    ]
    assert post_layout(admin, board_id, layout).json() == {"ok": True}
    saved = {
        t["id"]: (t["x"], t["y"], t["w"], t["h"]) for t in board(data_dir)["tiles"]
    }
    assert saved == {a["id"]: (4, 0, 2, 2), b["id"]: (0, 3, 1, 1)}


@pytest.mark.parametrize(
    "change, error",
    [
        ({"w": 3, "h": 1}, "layout_bad_size"),
        ({"x": 5, "w": 2, "h": 1}, "layout_outside"),
        ({"x": -1}, "layout_outside"),
        ({"x": "left"}, "layout_invalid"),
        ({"x": 1, "y": 0}, "layout_overlap"),
    ],
)
def test_bad_layouts_are_refused(admin, data_dir, board_id, change, error):
    add(admin, board_id, type="link", name="A", url="http://a.lan")
    add(admin, board_id, type="link", name="B", url="http://b.lan")
    a, b = board(data_dir)["tiles"]
    first = {"id": a["id"], "x": 0, "y": 0, "w": 1, "h": 1}
    second = {"id": b["id"], "x": 1, "y": 0, "w": 1, "h": 1}
    if error == "layout_overlap":
        second.update(x=0)
    else:
        first.update(change)
    response = post_layout(admin, board_id, [first, second])
    assert response.status_code == 400
    assert response.json()["error"] == error


def test_layout_must_list_every_tile_once(admin, data_dir, board_id):
    add(admin, board_id, type="link", name="A", url="http://a.lan")
    tile = board(data_dir)["tiles"][0]
    item = {"id": tile["id"], "x": 0, "y": 0, "w": 1, "h": 1}
    assert (
        post_layout(admin, board_id, [item, item]).json()["error"]
        == "layout_tiles_mismatch"
    )
    assert post_layout(admin, board_id, []).json()["error"] == "layout_tiles_mismatch"


def test_layout_needs_session_and_csrf_header(admin, board_id):
    assert post_layout(admin, board_id, [], csrf="wrong").status_code == 403
    stranger = TestClient(app, follow_redirects=False)
    response = stranger.post(
        f"/edit/{board_id}/layout", json=[], headers={"X-CSRF-Token": admin.csrf}
    )
    assert response.status_code == 401


def test_second_tab_has_its_own_address(admin, data_dir, board_id):
    admin.post("/settings/dashboards", data={"csrf": admin.csrf, "name": "Medien"})
    second = json.loads((data_dir / "portal.json").read_text())["dashboards"][1]
    add(admin, second["id"], type="link", name="Jellyfin", url="http://nas.lan:8096")
    page = admin.get(f"/d/{second['id']}").text
    assert "Jellyfin" in page
    assert "Jellyfin" not in admin.get("/").text
    assert admin.get("/d/doesnotexist").status_code == 404
