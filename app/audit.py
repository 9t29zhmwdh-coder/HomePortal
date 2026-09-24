"""Audit trail and error references, written to stdout for `docker compose logs`.

Every request that changes something (setup, login, logout, settings, edit mode)
leaves one JSON line: who, what, when, from where, and whether it worked. Form
contents are never logged, so passwords and tokens cannot end up in the log.
The application only appends to stdout; it has no way to rewrite earlier lines.
"""

import json
import logging
import secrets
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

AUDITED_PREFIXES = ("/setup", "/login", "/logout", "/settings", "/edit")

logger = logging.getLogger("homeportal.audit")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def is_audited(method: str, path: str) -> bool:
    return method == "POST" and path.startswith(AUDITED_PREFIXES)


def outcome_of(status: int, location: str) -> str:
    """Routes answer changes with a redirect; an ?err= in it names what went wrong."""
    if status >= 400:
        return f"http_{status}"
    errors = parse_qs(urlparse(location).query).get("err")
    return errors[0] if errors else "ok"


def record(event: dict) -> None:
    event["time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    logger.info(json.dumps(event, ensure_ascii=False))


def request_event(method, path, client, logged_in, status, location) -> dict:
    return {
        "kind": "audit",
        "action": f"{method} {path}",
        "actor": "admin" if logged_in else "anonymous",
        "client": client,
        "outcome": outcome_of(status, location),
    }


def new_reference() -> str:
    return secrets.token_hex(4)


def record_error(reference: str, method: str, path: str, error: BaseException) -> None:
    logging.getLogger("homeportal").error(
        "unhandled error, reference %s, %s %s", reference, method, path, exc_info=error
    )
