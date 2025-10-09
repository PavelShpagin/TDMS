from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings, get_static_dir, get_templates_dir
from .lifespan import lifespan
from .routers import databases, tables, sync, drive, persistence, operations


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_title, lifespan=lifespan)

    # Static and templates
    templates = Jinja2Templates(directory=str(get_templates_dir()))
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(get_static_dir())), name="static")

    # Routers
    app.include_router(databases.router)
    app.include_router(tables.router)
    app.include_router(sync.router)
    app.include_router(drive.router)
    app.include_router(persistence.router)
    app.include_router(operations.router)

    return app


