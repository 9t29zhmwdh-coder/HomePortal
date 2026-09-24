"""The settings page and every route that changes the portal. All of them need a login."""

from fastapi import APIRouter, Depends, Request, UploadFile

from app import auth, catalog, store, uploads, web
from app import portal as portal_data

router = APIRouter(prefix="/settings")
TEXT_FIELDS = ("title", "subtitle", "links_heading", "album_heading")
MAX_TEXT = 200


@router.get("")
async def settings_page(request: Request, msg: str = "", err: str = ""):
    web.require_admin(request)
    return web.render(
        request,
        "settings.html",
        web.load_state(),
        uploads=uploads.list_uploads(web.data_dir()),
        msg=msg,
        err=err,
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


def link_fields(form) -> dict | None:
    fields = {
        key: str(form.get(key, ""))[:MAX_TEXT].strip()
        for key in ("name", "url", "description", "icon")
    }
    if not fields["name"] or not portal_data.is_safe_url(fields["url"]):
        return None
    return fields


@router.post("/links", dependencies=[Depends(web.require_admin_form)])
async def add_link(request: Request):
    fields = link_fields(await request.form())
    if fields is None:
        return web.redirect("/settings?err=invalid_link#links")
    store.update(
        web.data_dir(), lambda state: state["links"].append(store.new_link(fields))
    )
    return web.redirect("/settings?msg=saved#links")


@router.post("/links/{link_id}", dependencies=[Depends(web.require_admin_form)])
async def edit_link(request: Request, link_id: str):
    form = await request.form()
    action = form.get("action")
    fields = link_fields(form)
    if action == "save" and fields is None:
        return web.redirect("/settings?err=invalid_link#links")
    store.update(
        web.data_dir(),
        lambda state: apply_link_action(state["links"], link_id, action, fields),
    )
    return web.redirect("/settings?msg=saved#links")


def apply_link_action(links: list, link_id: str, action, fields) -> None:
    index = next((i for i, link in enumerate(links) if link["id"] == link_id), None)
    if index is None:
        return
    if action == "save":
        links[index].update(fields)
    elif action == "delete":
        links.pop(index)
    elif action in ("up", "down"):
        target = index - 1 if action == "up" else index + 1
        if 0 <= target < len(links):
            links[index], links[target] = links[target], links[index]


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
