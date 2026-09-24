"""The settings page and every route that changes the portal. All of them need a login."""

from fastapi import APIRouter, Depends, Request, UploadFile

from app import auth, catalog, connections, live, store, tiles, uploads, web
from app import portal as portal_data

router = APIRouter(prefix="/settings")
TEXT_FIELDS = ("title", "subtitle")
MAX_NAME = 40
MAX_URL = 300
MAX_TEXT = 200


@router.get("")
async def settings_page(
    request: Request, msg: str = "", err: str = "", confirm_tab: str = ""
):
    web.require_admin(request)
    return web.render(
        request,
        "settings.html",
        web.load_state(),
        uploads=uploads.list_uploads(web.data_dir()),
        msg=msg,
        err=err,
        confirm_tab=confirm_tab,
        ha=ha_summary(),
    )


def ha_summary() -> dict:
    """What the page may know about the HA connection: the address, never the token."""
    ha = connections.load(web.data_dir()).get("home_assistant") or {}
    return {"url": ha.get("url", ""), "has_token": bool(ha.get("token"))}


@router.post("/appearance", dependencies=[Depends(web.require_admin_form)])
async def save_appearance(request: Request):
    form = await request.form()
    kind, _, value = str(form.get("background", "none:")).partition(":")
    names = uploads.list_uploads(web.data_dir())
    if not catalog.is_valid_background(kind, value, names):
        kind, value = "none", ""

    def change(state):
        look = state["appearance"]
        look["theme"] = pick(form.get("theme"), catalog.THEMES, look["theme"])
        look["font"] = pick(form.get("font"), catalog.FONTS, look["font"])
        look["language"] = pick(
            form.get("language"), catalog.LANGUAGES, look["language"]
        )
        look["background"] = {"kind": kind, "value": value}

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#appearance")


def pick(value, allowed, fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


@router.post("/texts", dependencies=[Depends(web.require_admin_form)])
async def save_texts(request: Request):
    form = await request.form()

    def change(state):
        for field in TEXT_FIELDS:
            state["site"][field] = str(form.get(field, ""))[:MAX_TEXT].strip()

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#texts")


@router.post("/dashboards", dependencies=[Depends(web.require_admin_form)])
async def add_dashboard(request: Request):
    form = await request.form()
    name = str(form.get("name", ""))[:MAX_NAME].strip()
    app_url = app_url_from(form)
    if app_url is None:
        return web.redirect("/settings?err=invalid_app_url#dashboards")

    def change(state):
        if name and len(state["dashboards"]) < tiles.MAX_DASHBOARDS:
            board = store.new_dashboard(name)
            if app_url:
                board["app_url"] = app_url
            state["dashboards"].append(board)

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#dashboards")


def app_url_from(form) -> str | None:
    """Empty means a tab of tiles; otherwise it must be a safe address. None: refused."""
    url = str(form.get("app_url", ""))[:MAX_URL].strip()
    if url and not portal_data.is_safe_url(url):
        return None
    return url


@router.post(
    "/dashboards/{dashboard_id}", dependencies=[Depends(web.require_admin_form)]
)
async def edit_dashboard(request: Request, dashboard_id: str):
    form = await request.form()
    action = form.get("action")
    name = str(form.get("name", ""))[:MAX_NAME].strip()
    app_url = app_url_from(form)
    if app_url is None:
        return web.redirect("/settings?err=invalid_app_url#dashboards")
    if action == "delete" and form.get("confirm") != "yes":
        board = store.find_dashboard(web.load_state(), dashboard_id)
        target = f"?confirm_tab={board['id']}" if board else ""
        return web.redirect(f"/settings{target}#dashboards")
    store.update(
        web.data_dir(),
        lambda state: apply_dashboard_action(
            state["dashboards"], dashboard_id, action, name, app_url
        ),
    )
    return web.redirect("/settings?msg=saved#dashboards")


def apply_dashboard_action(
    boards: list, board_id: str, action, name: str, app_url: str = ""
) -> None:
    index = next((i for i, board in enumerate(boards) if board["id"] == board_id), None)
    if index is None:
        return
    if action == "rename":
        boards[index]["name"] = name
        boards[index]["app_url"] = app_url
    elif action == "delete" and len(boards) > 1:
        boards.pop(index)
    elif action in ("up", "down"):
        target = index - 1 if action == "up" else index + 1
        if 0 <= target < len(boards):
            boards[index], boards[target] = boards[target], boards[index]


@router.post("/uploads", dependencies=[Depends(web.require_admin_form)])
async def upload_background(image: UploadFile):
    try:
        name = uploads.save_upload(
            web.data_dir(), await image.read(uploads.MAX_UPLOAD_BYTES + 1)
        )
    except uploads.UploadError as error:
        return web.redirect(f"/settings?err={error}#appearance")

    def change(state):
        state["appearance"]["background"] = {"kind": "upload", "value": name}

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#appearance")


@router.post("/uploads/{name}/delete", dependencies=[Depends(web.require_admin_form)])
async def delete_background(name: str):
    uploads.delete_upload(web.data_dir(), name)

    def change(state):
        if state["appearance"]["background"] == {"kind": "upload", "value": name}:
            state["appearance"]["background"] = {"kind": "none", "value": ""}

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#appearance")


@router.post("/access", dependencies=[Depends(web.require_admin_form)])
async def save_access(request: Request):
    form = await request.form()
    required = form.get("require_login") == "on"
    store.update(
        web.data_dir(),
        lambda state: state["access"].update(require_login_to_view=required),
    )
    return web.redirect("/settings?msg=saved#access")


@router.post("/password", dependencies=[Depends(web.require_admin_form)])
async def change_password(request: Request):
    form = await request.form()
    password, confirm = str(form.get("password", "")), str(form.get("confirm", ""))
    problem = auth.password_problem(password, confirm)
    if problem:
        return web.redirect(f"/settings?err={problem}#access")
    auth.set_password(web.data_dir(), password)
    # The new key signed out every session, this one included.
    return web.redirect("/login")


@router.post("/connections/ha", dependencies=[Depends(web.require_admin_form)])
async def save_home_assistant(request: Request):
    form = await request.form()
    url, token = str(form.get("url", "")), str(form.get("token", ""))
    problem = connections.set_home_assistant(web.data_dir(), url, token)
    if problem:
        return web.redirect(f"/settings?err={problem}#connections")
    live.clear_cache()
    return await test_home_assistant()


@router.post("/connections/ha/test", dependencies=[Depends(web.require_admin_form)])
async def test_home_assistant():
    ha = connections.home_assistant(web.data_dir())
    if ha is None:
        return web.redirect("/settings?err=ha_not_connected#connections")
    result = await live.check_home_assistant(ha["url"], ha["token"])
    kind = "msg" if result == "ha_ok" else "err"
    return web.redirect(f"/settings?{kind}={result}#connections")


@router.post("/connections/ha/forget", dependencies=[Depends(web.require_admin_form)])
async def forget_home_assistant():
    connections.forget_home_assistant(web.data_dir())
    live.clear_cache()
    return web.redirect("/settings?msg=saved#connections")
