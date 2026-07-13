from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert "Home Portal" in response.text


def test_static_css_is_served():
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
