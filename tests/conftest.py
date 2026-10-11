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


def setup_form(data_dir, password=PASSWORD, confirm=None):
    """The /setup form data, with the one-time token the owner would read from the log."""
    return {
        "password": password,
        "confirm": password if confirm is None else confirm,
        "token": auth.ensure_setup_token(data_dir),
    }


@pytest.fixture
def admin(client, data_dir):
    """A client that has set the password and holds a session; .csrf is the form token."""
    response = client.post("/setup", data=setup_form(data_dir))
    assert response.status_code == 303
    client.data_dir = data_dir
    client.csrf = csrf_from(client.get("/settings").text)
    return client


def csrf_from(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)
