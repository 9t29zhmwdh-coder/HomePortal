from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import portal as portal_data

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Home Portal", version="1.2.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["caption_for"] = portal_data.caption_for


@app.get("/")
async def index(request: Request):
    portal = portal_data.load_portal(portal_data.DATA_DIR)
    context = {"portal": portal, "data_dir": str(portal_data.DATA_DIR)}
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/photos/{name}")
async def photo(name: str):
    path = portal_data.resolve_photo(name, portal_data.DATA_DIR)
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
