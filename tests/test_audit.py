import json
import logging

import pytest

from app import audit, store
from tests.conftest import PASSWORD


@pytest.fixture
def audit_lines():
    lines: list[str] = []

    class Collect(logging.Handler):
        def emit(self, record):
            lines.append(record.getMessage())

    handler = Collect()
    audit.logger.addHandler(handler)
    yield lines
    audit.logger.removeHandler(handler)


def events(lines):
    return [json.loads(line) for line in lines]


def test_changes_are_audited_without_their_content(client, audit_lines):
    client.post("/setup", data={"password": PASSWORD, "confirm": PASSWORD})
    client.post("/login", data={"password": "wrong-password-123"})
    logged = events(audit_lines)
    assert [e["action"] for e in logged] == ["POST /setup", "POST /login"]
    assert logged[0]["outcome"] == "ok" and logged[0]["actor"] == "anonymous"
    assert logged[1]["outcome"] == "login_failed"
    assert all(e["client"] and e["time"] for e in logged)
    assert PASSWORD not in "".join(audit_lines)
    assert "wrong-password-123" not in "".join(audit_lines)


def test_admin_actions_name_the_admin(admin, audit_lines):
    admin.post("/settings/texts", data={"csrf": admin.csrf, "title": "x"})
    admin.post("/settings/texts", data={"title": "no csrf"})
    first, second = events(audit_lines)
    assert first["actor"] == "admin" and first["outcome"] == "ok"
    assert second["outcome"] == "http_403"


def test_reading_is_not_audited(admin, audit_lines):
    admin.get("/")
    admin.get("/settings")
    assert audit_lines == []


def test_unexpected_errors_show_only_a_reference(client, monkeypatch, caplog):
    def broken(_data_dir):
        raise RuntimeError("disk on fire at /data/portal.json")

    monkeypatch.setattr(store, "load", broken)
    with caplog.at_level(logging.ERROR, logger="homeportal"):
        response = client.get("/")
    assert response.status_code == 500
    assert "Reference:" in response.text
    assert "/data/portal.json" not in response.text
    reference = response.text.rsplit(" ", 1)[-1]
    assert reference in caplog.text and "disk on fire" in caplog.text
