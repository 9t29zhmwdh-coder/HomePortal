import re
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import auth
from app import portal as portal_data
from app.main import app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
PASSWORD = "korrekt-pferd-batterie"


@pytest.fixture(autouse=True)
def reset_lockout():
    auth._failures.clear()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(portal_data, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client(data_dir):
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def example_data(data_dir):
    shutil.copy(EXAMPLES / "portal.yaml", data_dir / "portal.yaml")
    shutil.copytree(EXAMPLES / "photos", data_dir / "photos")
    return data_dir


@pytest.fixture
def admin(client):
    """A client that has set the password and holds a session; .csrf is the form token."""
    response = client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    assert response.status_code == 303
    client.csrf = csrf_from(client.get("/settings").text)
    return client


def csrf_from(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)
