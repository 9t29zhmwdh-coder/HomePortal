import io
import json

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.conftest import PASSWORD


def state(data_dir) -> dict:
    return json.loads((data_dir / "portal.json").read_text())


def jpeg_with_gps() -> bytes:
    image = Image.new("RGB", (800, 600), "orange")
    exif = Image.Exif()
    exif[0x8825] = {1: "N", 2: (47.0, 23.0, 0.0), 3: "E", 4: (8.0, 3.0, 0.0)}
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


def test_login_with_wrong_password_fails_and_locks_after_five(client, admin):
    fresh = TestClient(app, follow_redirects=False)
    for _ in range(5):
        assert (
            "login_failed"
            in fresh.post("/login", data={"password": "falsch"}).headers["location"]
        )
    locked = fresh.post("/login", data={"password": PASSWORD})
    assert "login_locked" in locked.headers["location"]


def test_login_with_right_password_opens_settings(admin):
    fresh = TestClient(app, follow_redirects=False)
    response = fresh.post("/login", data={"password": PASSWORD})
    assert response.headers["location"] == "/settings"
    assert fresh.get("/settings").status_code == 200


def test_changes_need_a_session(client, admin):
    stranger = TestClient(app, follow_redirects=False)
    response = stranger.post(
        "/settings/appearance", data={"csrf": admin.csrf, "theme": "paper"}
    )
    assert response.headers["location"] == "/login"


def test_changes_need_the_csrf_token(admin):
    assert (
        admin.post("/settings/appearance", data={"theme": "paper"}).status_code == 403
    )
    assert (
        admin.post(
            "/settings/appearance", data={"csrf": "wrong", "theme": "paper"}
        ).status_code
        == 403
    )


def test_appearance_is_saved_and_rendered(admin, data_dir):
    form = {
        "csrf": admin.csrf,
        "theme": "playful",
        "font": "fredoka",
        "language": "de",
        "background": "pattern:bubbles",
    }
    admin.post("/settings/appearance", data=form)
    look = state(data_dir)["appearance"]
    assert look == {
        "theme": "playful",
        "font": "fredoka",
        "language": "de",
        "background": {"kind": "pattern", "value": "bubbles"},
    }
    body = admin.get("/").text
    assert 'class="theme-playful bg-pattern bg-bubbles"' in body
    assert "Fredoka Variable" in body


def test_unknown_values_fall_back(admin, data_dir):
    form = {
        "csrf": admin.csrf,
        "theme": "hacker",
        "font": "comic",
        "language": "xx",
        "background": "photo:../../etc",
    }
    admin.post("/settings/appearance", data=form)
    look = state(data_dir)["appearance"]
    assert (
        look["theme"] == "midnight"
        and look["font"] == "inter"
        and look["language"] == "auto"
    )
    assert look["background"] == {"kind": "none", "value": ""}


def test_tabs_can_be_added_renamed_moved_and_deleted_with_confirmation(admin, data_dir):
    admin.get("/")
    admin.post("/settings/dashboards", data={"csrf": admin.csrf, "name": "Medien"})
    first, second = state(data_dir)["dashboards"]
    form = {"csrf": admin.csrf, "action": "up"}
    admin.post(f"/settings/dashboards/{second['id']}", data=form)
    assert [b["name"] for b in state(data_dir)["dashboards"]] == ["Medien", ""]
    rename = {"csrf": admin.csrf, "action": "rename", "name": "Zuhause"}
    admin.post(f"/settings/dashboards/{first['id']}", data=rename)
    unconfirmed = admin.post(
        f"/settings/dashboards/{second['id']}",
        data={"csrf": admin.csrf, "action": "delete"},
    )
    assert "confirm_tab" in unconfirmed.headers["location"]
    assert len(state(data_dir)["dashboards"]) == 2
    confirmed = {"csrf": admin.csrf, "action": "delete", "confirm": "yes"}
    admin.post(f"/settings/dashboards/{second['id']}", data=confirmed)
    assert [b["name"] for b in state(data_dir)["dashboards"]] == ["Zuhause"]


def test_last_tab_cannot_be_deleted(admin, data_dir):
    admin.get("/")
    only = state(data_dir)["dashboards"][0]
    confirmed = {"csrf": admin.csrf, "action": "delete", "confirm": "yes"}
    admin.post(f"/settings/dashboards/{only['id']}", data=confirmed)
    assert len(state(data_dir)["dashboards"]) == 1


def test_html_in_texts_is_escaped(admin):
    admin.post(
        "/settings/texts", data={"csrf": admin.csrf, "title": "<script>x</script>"}
    )
    body = admin.get("/").text
    assert "<script>x</script>" not in body
    assert "&lt;script&gt;" in body


def test_upload_strips_location_data_and_becomes_background(admin, data_dir):
    files = {"image": ("holiday.jpg", jpeg_with_gps(), "image/jpeg")}
    admin.post("/settings/uploads", data={"csrf": admin.csrf}, files=files)
    background = state(data_dir)["appearance"]["background"]
    assert background["kind"] == "upload"
    stored = data_dir / "uploads" / f"{background['value']}.jpg"
    assert 0x8825 not in Image.open(stored).getexif()
    assert admin.get(f"/media/{background['value']}").status_code == 200
    assert admin.get(f"/media/{background['value']}?thumb=true").status_code == 200


def test_non_images_are_refused(admin, data_dir):
    files = {"image": ("evil.jpg", b"<?php echo 1; ?>", "image/jpeg")}
    response = admin.post("/settings/uploads", data={"csrf": admin.csrf}, files=files)
    assert "upload_not_an_image" in response.headers["location"]
    assert not (data_dir / "uploads").exists() or not any(
        (data_dir / "uploads").iterdir()
    )


def test_deleting_the_active_upload_resets_the_background(admin, data_dir):
    files = {"image": ("a.jpg", jpeg_with_gps(), "image/jpeg")}
    admin.post("/settings/uploads", data={"csrf": admin.csrf}, files=files)
    name = state(data_dir)["appearance"]["background"]["value"]
    admin.post(f"/settings/uploads/{name}/delete", data={"csrf": admin.csrf})
    assert state(data_dir)["appearance"]["background"] == {"kind": "none", "value": ""}
    assert admin.get(f"/media/{name}").status_code == 404


def test_require_login_protects_page_photos_and_uploads(admin, example_data):
    files = {"image": ("a.jpg", jpeg_with_gps(), "image/jpeg")}
    admin.post("/settings/uploads", data={"csrf": admin.csrf}, files=files)
    upload = state(example_data)["appearance"]["background"]["value"]
    admin.post("/settings/access", data={"csrf": admin.csrf, "require_login": "on"})
    stranger = TestClient(app, follow_redirects=False)
    for path in ("/", "/photos/beach-day.jpg", f"/media/{upload}"):
        assert stranger.get(path).headers.get("location") == "/login", path
    assert admin.get("/").status_code == 200


def test_changing_the_password_ends_every_session(admin):
    other = TestClient(app, follow_redirects=False)
    other.post("/login", data={"password": PASSWORD})
    new = "ganz-neues-passwort"
    admin.post(
        "/settings/password", data={"csrf": admin.csrf, "password": new, "confirm": new}
    )
    assert admin.get("/settings").headers["location"] == "/login"
    assert other.get("/settings").headers["location"] == "/login"


def test_iphone_heic_upload_is_accepted(admin, data_dir):
    from pillow_heif import register_heif_opener

    register_heif_opener()
    buffer = io.BytesIO()
    Image.new("RGB", (640, 480), "teal").save(buffer, "HEIF")
    files = {"image": ("IMG_0001.HEIC", buffer.getvalue(), "image/heic")}
    admin.post("/settings/uploads", data={"csrf": admin.csrf}, files=files)
    background = state(data_dir)["appearance"]["background"]
    assert background["kind"] == "upload"
    stored = Image.open(data_dir / "uploads" / f"{background['value']}.jpg")
    assert stored.format == "JPEG" and stored.size == (640, 480)
