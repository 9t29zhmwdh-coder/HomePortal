"""Edit mode for one tab: drag tiles into place, pick sizes, add, change and remove tiles."""

from zoneinfo import available_timezones

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app import connections, i18n, live, store, tiles, web
from app import portal as portal_data

router = APIRouter(prefix="/edit")
MAX_TEXT = 200
MAX_NOTE = 2000


def board_or_404(state: dict, dashboard_id: str) -> dict:
    board = store.find_dashboard(state, dashboard_id)
    if board is None:
        raise HTTPException(status_code=404)
    return board


def tile_or_404(board: dict, tile_id: str) -> dict:
    tile = store.find_tile(board, tile_id)
    if tile is None:
        raise HTTPException(status_code=404)
    return tile


@router.get("/{dashboard_id}")
async def edit_page(request: Request, dashboard_id: str, err: str = ""):
    web.require_admin(request)
    state = web.load_state()
    board = board_or_404(state, dashboard_id)
    photos = portal_data.list_photos(web.data_dir())
    return web.render(request, "edit.html", state, board=board, photos=photos, err=err)


@router.post("/{dashboard_id}/layout", dependencies=[Depends(web.require_admin_json)])
async def save_layout(request: Request, dashboard_id: str):
    layout = await request.json()
    if not isinstance(layout, list):
        return JSONResponse({"error": "layout_invalid"}, status_code=400)
    board = board_or_404(web.load_state(), dashboard_id)
    problem = tiles.layout_problem(board["tiles"], layout)
    if problem:
        return JSONResponse({"error": problem}, status_code=400)

    def change(state):
        tiles.apply_layout(board_or_404(state, dashboard_id)["tiles"], layout)

    store.update(web.data_dir(), change)
    return {"ok": True}


@router.get("/{dashboard_id}/tiles/new")
async def new_tile_page(
    request: Request, dashboard_id: str, type: str = "link", err: str = ""
):
    web.require_admin(request)
    state = web.load_state()
    board = board_or_404(state, dashboard_id)
    if type not in tiles.TYPES:
        raise HTTPException(status_code=404)
    blank = {"id": "", "type": type, "config": {}}
    return render_form(request, state, board, blank, err)


@router.post("/{dashboard_id}/tiles", dependencies=[Depends(web.require_admin_form)])
async def create_tile(request: Request, dashboard_id: str):
    form = await request.form()
    board = board_or_404(web.load_state(), dashboard_id)
    # Redirects are built only from values found in the stored data or the type list,
    # never from the request itself.
    tile_type = next((key for key in tiles.TYPES if key == form.get("type")), None)
    if tile_type is None:
        raise HTTPException(status_code=404)
    config = await tile_config(tile_type, form, request)
    if config is None:
        return web.redirect(
            f"/edit/{board['id']}/tiles/new?type={tile_type}&err=invalid_{tile_type}"
        )

    def change(state):
        board = board_or_404(state, dashboard_id)
        if len(board["tiles"]) < tiles.MAX_TILES:
            board["tiles"].append(tiles.new_tile(tile_type, config, board["tiles"]))

    store.update(web.data_dir(), change)
    return web.redirect(f"/edit/{board['id']}")


@router.get("/{dashboard_id}/tiles/{tile_id}")
async def tile_page(request: Request, dashboard_id: str, tile_id: str, err: str = ""):
    web.require_admin(request)
    state = web.load_state()
    board = board_or_404(state, dashboard_id)
    tile = tile_or_404(board, tile_id)
    return render_form(request, state, board, tile, err)


def render_form(request: Request, state: dict, board: dict, tile: dict, err: str):
    connected = connections.home_assistant(web.data_dir()) is not None
    return web.render(
        request,
        "tile_form.html",
        state,
        board=board,
        tile=tile,
        err=err,
        ha_connected=connected,
    )


@router.post(
    "/{dashboard_id}/tiles/{tile_id}", dependencies=[Depends(web.require_admin_form)]
)
async def save_tile(request: Request, dashboard_id: str, tile_id: str):
    form = await request.form()
    board = board_or_404(web.load_state(), dashboard_id)
    tile = tile_or_404(board, tile_id)
    config = await tile_config(tile["type"], form, request)
    if config is None:
        return web.redirect(
            f"/edit/{board['id']}/tiles/{tile['id']}?err=invalid_{tile['type']}"
        )

    def change(state):
        tile_or_404(board_or_404(state, dashboard_id), tile_id)["config"] = config

    store.update(web.data_dir(), change)
    return web.redirect(f"/edit/{board['id']}")


@router.post(
    "/{dashboard_id}/tiles/{tile_id}/delete",
    dependencies=[Depends(web.require_admin_form)],
)
async def delete_tile(dashboard_id: str, tile_id: str):
    board_id = board_or_404(web.load_state(), dashboard_id)["id"]

    def change(state):
        board = board_or_404(state, dashboard_id)
        board["tiles"] = [tile for tile in board["tiles"] if tile["id"] != tile_id]

    store.update(web.data_dir(), change)
    return web.redirect(f"/edit/{board_id}")


async def tile_config(tile_type: str, form, request: Request) -> dict | None:
    def text(key: str, limit: int = MAX_TEXT) -> str:
        return str(form.get(key, ""))[:limit].strip()

    if tile_type == "weather":
        return await weather_config(text("place"), request)
    builder = CONFIG_BUILDERS.get(tile_type)
    return builder(text) if builder else None


def link_config(text) -> dict | None:
    config = {key: text(key) for key in ("name", "url", "description", "icon")}
    if not config["name"] or not portal_data.is_safe_url(config["url"]):
        return None
    return config


def ha_config(text) -> dict | None:
    entities = live.parse_entities(text("entities", 2000))
    return {"title": text("title"), "entities": entities} if entities else None


def status_config(text) -> dict | None:
    config = {key: text(key) for key in ("name", "url", "icon")}
    if not config["name"] or not portal_data.is_safe_url(config["url"]):
        return None
    return config


def clock_config(text) -> dict | None:
    zone = text("timezone")
    if zone and zone not in available_timezones():
        return None
    return {"title": text("title"), "timezone": zone}


async def weather_config(place: str, request: Request) -> dict | None:
    if not place:
        return None
    language = i18n.pick_language(
        web.load_state()["appearance"]["language"],
        request.headers.get("accept-language"),
    )
    return await live.geocode(place, language)


CONFIG_BUILDERS = {
    "link": link_config,
    "note": lambda text: {"title": text("title"), "text": text("text", MAX_NOTE)},
    "album": lambda text: {"title": text("title")},
    "ha": ha_config,
    "status": status_config,
    "clock": clock_config,
}
