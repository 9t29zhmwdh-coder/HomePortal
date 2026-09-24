from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import auth, editor, live, settings, store, tiles, uploads, web
from app import portal as portal_data

app = FastAPI(title="Home Portal", version="1.6.0")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # Home Portal itself must not be framed by other sites (clickjacking on the settings).
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response


app.mount("/static", StaticFiles(directory=str(web.BASE_DIR / "static")), name="static")
app.include_router(settings.router)
app.include_router(editor.router)


@app.exception_handler(web.LoginRequired)
async def to_login(request: Request, _exc: web.LoginRequired):
    target = "/login" if auth.is_set_up(web.data_dir()) else "/setup"
    return web.redirect(target)


@app.get("/")
async def index(request: Request):
    return await show_dashboard(request, None)


@app.get("/d/{dashboard_id}")
async def dashboard(request: Request, dashboard_id: str):
    return await show_dashboard(request, dashboard_id)


async def show_dashboard(request: Request, dashboard_id: str | None):
    state = web.load_state()
    guard_viewing(request, state)
    board = store.find_dashboard(state, dashboard_id)
    if board is None:
        raise HTTPException(status_code=404)
    photos = portal_data.list_photos(web.data_dir())
    origin = str(request.base_url)
    values = await live.board_data(board, web.data_dir(), origin)
    if board.get("app_url"):
        values["tab-app"] = await live.embed_status(board["app_url"], origin)
    return web.render(
        request, "index.html", state, board=board, photos=photos, live=values
    )


@app.get("/live/{dashboard_id}/{tile_id}")
async def live_tile(request: Request, dashboard_id: str, tile_id: str):
    """One tile rendered again with fresh values; live.js swaps it in every 30 seconds."""
    state = web.load_state()
    guard_viewing(request, state)
    board = store.find_dashboard(state, dashboard_id)
    tile = store.find_tile(board, tile_id) if board else None
    if tile is None or tile["type"] not in tiles.LIVE_TYPES:
        raise HTTPException(status_code=404)
    values = {tile["id"]: await live.tile_data(tile, web.data_dir())}
    return web.render(request, "_live_fragment.html", state, tile=tile, live=values)


def guard_viewing(request: Request, state: dict) -> None:
    if state["access"]["require_login_to_view"] and auth.is_set_up(web.data_dir()):
        web.require_admin(request)


@app.get("/photos/{name}")
async def photo(request: Request, name: str):
    guard_viewing(request, web.load_state())
    return file_or_404(portal_data.resolve_photo(name, web.data_dir()))


@app.get("/media/{name}")
async def media(request: Request, name: str, thumb: bool = False):
    guard_viewing(request, web.load_state())
    return file_or_404(uploads.resolve_upload(web.data_dir(), name, thumb))


def file_or_404(path):
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path)


@app.get("/setup")
async def setup_page(request: Request, err: str = ""):
    if auth.is_set_up(web.data_dir()):
        return web.redirect("/login")
    return web.render(request, "setup.html", web.load_state(), err=err)


@app.post("/setup")
async def setup(password: str = Form(""), confirm: str = Form("")):
    if auth.is_set_up(web.data_dir()):
        raise HTTPException(status_code=403)
    problem = auth.password_problem(password, confirm)
    if problem:
        return web.redirect(f"/setup?err={problem}")
    auth.set_password(web.data_dir(), password)
    return logged_in_redirect("/settings")


@app.get("/login")
async def login_page(request: Request, err: str = ""):
    if not auth.is_set_up(web.data_dir()):
        return web.redirect("/setup")
    return web.render(request, "login.html", web.load_state(), err=err)


@app.post("/login")
async def login(request: Request, password: str = Form("")):
    client = web.client_id(request)
    if auth.is_locked_out(client):
        return web.redirect("/login?err=login_locked")
    if not auth.check_password(web.data_dir(), password):
        auth.record_failure(client)
        return web.redirect("/login?err=login_failed")
    auth.clear_failures(client)
    return logged_in_redirect("/settings")


@app.post("/logout")
async def logout():
    response = web.redirect("/")
    response.delete_cookie(auth.COOKIE_NAME)
    return response


def logged_in_redirect(path: str):
    response = web.redirect(path)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.issue_session(web.data_dir()),
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,
        samesite="strict",
    )
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
