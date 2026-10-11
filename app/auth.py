"""One admin account: password hash and session key live in DATA_DIR/auth.json (mode 0600).

The page itself stays readable without a login on the home network unless the
admin turns that off; anything that changes the portal needs a session.
"""

import json
import os
import secrets
import threading
import time
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from itsdangerous import BadSignature, URLSafeTimedSerializer

AUTH_NAME = "auth.json"
COOKIE_NAME = "hp_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30
MIN_PASSWORD_LENGTH = 10
# Failed logins per client before it has to wait, and for how long.
MAX_FAILURES = 5
LOCKOUT_SECONDS = 300

_hasher = PasswordHasher()
_lock = threading.Lock()
_failures: dict[str, list[float]] = {}


def auth_path(data_dir: Path) -> Path:
    return data_dir / AUTH_NAME


def load_auth(data_dir: Path) -> dict:
    path = auth_path(data_dir)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_auth(data_dir: Path, auth: dict) -> None:
    path = auth_path(data_dir)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(auth, handle)


def is_set_up(data_dir: Path) -> bool:
    return bool(load_auth(data_dir).get("password_hash"))


def set_password(data_dir: Path, password: str) -> None:
    with _lock:
        auth = load_auth(data_dir)
        auth["password_hash"] = _hasher.hash(password)
        # A new password also invalidates every existing session.
        auth["session_key"] = secrets.token_urlsafe(32)
        # The setup token has done its job.
        auth.pop("setup_token", None)
        write_auth(data_dir, auth)


def ensure_setup_token(data_dir: Path) -> str | None:
    """The one-time token that guards the first setup, created on first need.

    It is written to the container log, so only someone who can read the log (the
    owner) can claim the admin account. None once a password exists.
    """
    with _lock:
        auth = load_auth(data_dir)
        if auth.get("password_hash"):
            return None
        if not auth.get("setup_token"):
            auth["setup_token"] = secrets.token_urlsafe(16)
            write_auth(data_dir, auth)
            print(f"Home Portal setup token: {auth['setup_token']}", flush=True)
        return auth["setup_token"]


def check_setup_token(data_dir: Path, token: str) -> bool:
    expected = ensure_setup_token(data_dir)
    return expected is not None and secrets.compare_digest(expected, token.strip())


def check_password(data_dir: Path, password: str) -> bool:
    stored = load_auth(data_dir).get("password_hash", "")
    try:
        return _hasher.verify(stored, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_problem(password: str, confirm: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return "password_too_short"
    if password != confirm:
        return "password_mismatch"
    return None


def serializer(data_dir: Path) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(load_auth(data_dir)["session_key"], salt="session")


def issue_session(data_dir: Path) -> str:
    payload = {
        "csrf": secrets.token_urlsafe(24),
        "gen": load_auth(data_dir).get("session_gen", 0),
    }
    return serializer(data_dir).dumps(payload)


def revoke_sessions(data_dir: Path) -> None:
    """Logout: every cookie issued so far stops working, a stolen copy included."""
    with _lock:
        auth = load_auth(data_dir)
        auth["session_gen"] = auth.get("session_gen", 0) + 1
        write_auth(data_dir, auth)


def read_session(data_dir: Path, cookie: str | None) -> dict | None:
    if not cookie or not is_set_up(data_dir):
        return None
    try:
        session = serializer(data_dir).loads(cookie, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    if session.get("gen", 0) != load_auth(data_dir).get("session_gen", 0):
        return None
    return session


def is_locked_out(client: str) -> bool:
    now = time.monotonic()
    recent = [t for t in _failures.get(client, []) if now - t < LOCKOUT_SECONDS]
    _failures[client] = recent
    return len(recent) >= MAX_FAILURES


def record_failure(client: str) -> None:
    _failures.setdefault(client, []).append(time.monotonic())


def clear_failures(client: str) -> None:
    _failures.pop(client, None)
