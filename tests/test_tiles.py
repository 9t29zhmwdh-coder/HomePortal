from app import store, tiles


def test_schema_one_is_migrated_to_one_tab(tmp_path):
    (tmp_path / "photos").mkdir()
    (tmp_path / "photos" / "a.jpg").write_bytes(b"x")
    legacy = {
        "version": 1,
        "site": {
            "title": "Zuhause",
            "subtitle": "",
            "links_heading": "Dienste",
            "album_heading": "Ferien",
        },
        "links": [
            {
                "id": "x",
                "name": "NAS",
                "url": "http://nas.lan",
                "description": "",
                "icon": "",
            }
        ],
    }
    migrated = store.migrate(legacy, tmp_path)
    assert migrated["version"] == store.SCHEMA_VERSION
    assert migrated["site"] == {"title": "Zuhause", "subtitle": ""}
    (tab,) = migrated["dashboards"]
    assert tab["name"] == "Dienste"
    assert [t["type"] for t in tab["tiles"]] == ["link", "album"]
    assert tab["tiles"][1]["config"]["title"] == "Ferien"
    assert "links" not in migrated


def test_no_album_tile_without_photos(tmp_path):
    migrated = store.migrate({"version": 1, "links": []}, tmp_path)
    assert migrated["dashboards"][0]["tiles"] == []


def test_free_spot_fills_rows_left_to_right():
    placed: list = []
    for _ in range(7):
        placed.append(tiles.new_tile("link", {}, placed))
    assert [(t["x"], t["y"]) for t in placed] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
        (5, 0),
        (0, 1),
    ]


def test_wide_tile_skips_a_gap_that_is_too_small():
    placed = [
        {"id": "a", "type": "link", "x": 0, "y": 0, "w": 5, "h": 1, "config": {}},
    ]
    note = tiles.new_tile("note", {}, placed)
    assert (note["x"], note["y"]) == (0, 1)


def test_every_default_size_is_allowed_for_its_type():
    for name, spec in tiles.TYPES.items():
        w, h = tiles.SIZES[spec["default"]]
        assert tiles.is_allowed_size(name, w, h)
