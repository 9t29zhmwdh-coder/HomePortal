import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import portal as portal_data
from app.main import app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(portal_data, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client(data_dir):
    return TestClient(app)


def write_config(data_dir: Path, text: str) -> None:
    (data_dir / "portal.yaml").write_text(text, encoding="utf-8")


def test_without_config_shows_setup_hint_and_no_fake_links(client, data_dir):
    response = client.get("/")
    assert response.status_code == 200
    assert "portal.yaml" in response.text
    assert 'href="#"' not in response.text


def test_links_from_config_are_rendered(client, data_dir):
    shutil.copy(EXAMPLES / "portal.yaml", data_dir / "portal.yaml")
    response = client.get("/")
    assert 'href="http://192.168.1.10:5000"' in response.text
    assert "Home Assistant" in response.text
    assert "No links yet" not in response.text


def test_config_change_shows_without_restart(client, data_dir):
    write_config(data_dir, "links:\n  - {name: One, url: 'http://a.lan'}\n")
    assert "One" in client.get("/").text
    write_config(data_dir, "links:\n  - {name: Two, url: 'http://b.lan'}\n")
    assert "Two" in client.get("/").text


def test_headings_follow_config(client, data_dir):
    write_config(
        data_dir,
        "title: Zuhause\nlinks_heading: Dienste\nlinks:\n  - {name: NAS, url: 'http://n.lan'}\n",
    )
    text = client.get("/").text
    assert "<title>Zuhause</title>" in text
    assert "Dienste" in text


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "data:text/html,x", "ftp://x", "not a url"]
)
def test_unsafe_urls_are_dropped_and_reported(client, data_dir, url):
    write_config(data_dir, f"links:\n  - name: Bad\n    url: '{url}'\n")
    text = client.get("/").text
    assert 'class="link-card"' not in text
    assert "link 1 skipped" in text


def test_html_in_config_is_escaped(client, data_dir):
    write_config(
        data_dir, "links:\n  - {name: '<script>x</script>', url: 'http://a.lan'}\n"
    )
    text = client.get("/").text
    assert "<script>x</script>" not in text
    assert "&lt;script&gt;" in text


def test_broken_yaml_is_reported_not_a_500(client, data_dir):
    write_config(data_dir, "links: [unclosed\n")
    response = client.get("/")
    assert response.status_code == 200
    assert "could not be read" in response.text


def test_photos_are_listed_and_served(client, data_dir):
    photos = data_dir / "photos"
    photos.mkdir()
    shutil.copy(EXAMPLES / "photos" / "beach-day.jpg", photos / "beach-day.jpg")
    (photos / "notes.txt").write_text("not an image")
    (photos / ".hidden.jpg").write_bytes(b"x")
    text = client.get("/").text
    assert 'src="/photos/beach-day.jpg"' in text
    assert "Beach day" in text
    assert "notes.txt" not in text and ".hidden" not in text
    response = client.get("/photos/beach-day.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.parametrize(
    "name", ["notes.txt", ".hidden.jpg", "..%2Fportal.yaml", "missing.jpg"]
)
def test_only_listed_photos_are_served(client, data_dir, name):
    photos = data_dir / "photos"
    photos.mkdir()
    (photos / "notes.txt").write_text("secret")
    (photos / ".hidden.jpg").write_bytes(b"x")
    write_config(data_dir, "title: t\n")
    assert client.get(f"/photos/{name}").status_code == 404


def test_static_css_is_served(client):
    assert client.get("/static/css/style.css").status_code == 200


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}
