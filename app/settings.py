"""The settings page and every route that changes the portal. All of them need a login."""

from fastapi import APIRouter, Depends, Request, UploadFile

from app import auth, catalog, store, tiles, uploads, web

router = APIRouter(prefix="/settings")
TEXT_FIELDS = ("title", "subtitle")
MAX_NAME = 40
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
    )


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

    def change(state):
        if name and len(state["dashboards"]) < tiles.MAX_DASHBOARDS:
            state["dashboards"].append(store.new_dashboard(name))

    store.update(web.data_dir(), change)
    return web.redirect("/settings?msg=saved#dashboards")


@router.post(
    "/dashboards/{dashboard_id}", dependencies=[Depends(web.require_admin_form)]
)
async def edit_dashboard(request: Request, dashboard_id: str):
    form = await request.form()
    action = form.get("action")
    name = str(form.get("name", ""))[:MAX_NAME].strip()
    if action == "delete" and form.get("confirm") != "yes":
        return web.redirect(f"/settings?confirm_tab={dashboard_id}#dashboards")
    store.update(
        web.data_dir(),
        lambda state: apply_dashboard_action(
            state["dashboards"], dashboard_id, action, name
        ),
    )
    return web.redirect("/settings?msg=saved#dashboards")


def apply_dashboard_action(boards: list, board_id: str, action, name: str) -> None:
    index = next((i for i, board in enumerate(boards) if board["id"] == board_id), None)
    if index is None:
        return
    if action == "rename":
        boards[index]["name"] = name
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
