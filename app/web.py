"""Request helpers shared by the page and the settings routes."""

from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth, catalog, i18n, store
from app import portal as portal_data

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["caption_for"] = portal_data.caption_for
templates.env.globals["catalog"] = catalog


class LoginRequired(Exception):
    pass


def data_dir() -> Path:
    return portal_data.DATA_DIR


def session_of(request: Request) -> dict | None:
    return auth.read_session(data_dir(), request.cookies.get(auth.COOKIE_NAME))


def base_context(request: Request, state: dict) -> dict:
    language = i18n.pick_language(
        state["appearance"]["language"], request.headers.get("accept-language")
    )
    session = session_of(request)
    return {
        "state": state,
        "lang": language,
        "t": i18n.translator(language),
        "logged_in": session is not None,
        "csrf": session["csrf"] if session else "",
    }


def render(request: Request, template: str, state: dict, **extra):
    context = base_context(request, state) | extra
    return templates.TemplateResponse(request, template, context)


def require_admin(request: Request) -> dict:
    session = session_of(request)
    if session is None:
        raise LoginRequired
    return session


async def require_admin_form(request: Request) -> dict:
    """For POSTs: a valid session plus the matching CSRF token from the form."""
    session = require_admin(request)
    form = await request.form()
    if form.get("csrf") != session["csrf"]:
        raise HTTPException(status_code=403)
    return session


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


def client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def load_state() -> dict:
    return store.load(data_dir())
