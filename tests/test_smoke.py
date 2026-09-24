import json

import pytest

from tests.conftest import PASSWORD


def test_fresh_install_shows_hint_and_no_fake_links(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="#"' not in response.text
    assert "This tab is empty." in response.text


def test_legacy_yaml_becomes_tiles_once(client, example_data):
    text = client.get("/").text
    assert 'href="http://192.168.1.10:5000"' in text
    first = json.loads((example_data / "portal.json").read_text())
    client.get("/")
    second = json.loads((example_data / "portal.json").read_text())
    ids = [tile["id"] for tile in first["dashboards"][0]["tiles"]]
    assert ids == [tile["id"] for tile in second["dashboards"][0]["tiles"]]
    types = [tile["type"] for tile in first["dashboards"][0]["tiles"]]
    assert types == ["link"] * 4 + ["album"]


def test_page_follows_the_browser_language(client, example_data):
    text = client.get("/", headers={"accept-language": "de-CH,de;q=0.9"}).text
    assert '<html lang="de"' in text
    assert "Einstellungen" in text


def test_photos_are_listed_and_served(client, example_data):
    text = client.get("/").text
    assert 'src="/photos/beach-day.jpg"' in text
    assert "Beach day" in text
    response = client.get("/photos/beach-day.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.parametrize(
    "name", ["notes.txt", ".hidden.jpg", "..%2Fportal.yaml", "missing.jpg"]
)
def test_only_listed_photos_are_served(client, example_data, name):
    (example_data / "photos" / "notes.txt").write_text("secret")
    (example_data / "photos" / ".hidden.jpg").write_bytes(b"x")
    assert client.get(f"/photos/{name}").status_code == 404


@pytest.mark.parametrize("name", ["..%2Fauth", "nothing", "..%2F..%2Fetc%2Fpasswd"])
def test_media_only_serves_known_uploads(client, name):
    assert client.get(f"/media/{name}").status_code == 404


def test_static_assets_are_served(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/fonts/fredoka.woff2").status_code == 200
    assert client.get("/static/backgrounds/aurora.jpg").status_code == 200


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_settings_before_setup_leads_to_setup(client):
    assert client.get("/settings").headers["location"] == "/setup"
    assert client.get("/login").headers["location"] == "/setup"


def test_setup_rejects_short_or_mismatched_passwords(client, data_dir):
    short = client.post("/setup", data={"password": "kurz", "confirm": "kurz"})
    assert "password_too_short" in short.headers["location"]
    mismatch = client.post(
        "/setup", data={"password": PASSWORD, "confirm": PASSWORD + "x"}
    )
    assert "password_mismatch" in mismatch.headers["location"]
    assert not (data_dir / "auth.json").exists()


def test_setup_stores_only_a_hash_readable_by_the_owner(admin, data_dir):
    stored = (data_dir / "auth.json").read_text()
    assert PASSWORD not in stored
    assert "$argon2" in stored
    assert (data_dir / "auth.json").stat().st_mode & 0o077 == 0


def test_setup_cannot_run_twice(admin):
    other = "ein-anderes-passwort"
    assert (
        admin.post("/setup", data={"password": other, "confirm": other}).status_code
        == 403
    )
    assert admin.get("/setup").headers["location"] == "/login"


def test_logout_ends_the_session(admin):
    admin.post("/logout")
    assert admin.get("/settings").headers["location"] == "/login"
