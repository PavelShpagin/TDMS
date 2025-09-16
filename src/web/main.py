from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.database import Database

import json
import os
import io

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload, MediaIoBaseDownload
except Exception:  # pragma: no cover - optional dependency
    service_account = None
    build = None
    MediaInMemoryUpload = None
    MediaIoBaseDownload = None


app = FastAPI(title="Table Database")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Multi-database registry
_db_registry: Dict[str, Database] = {}
_active_db_name: str = "default"
_db_registry[_active_db_name] = Database(name=_active_db_name)


def get_db() -> Database:
    return _db_registry[_active_db_name]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    context = {"request": request, "tables": [t.to_json() for t in get_db().tables.values()]}
    return templates.TemplateResponse("index.html", context)


# Database management
@app.get("/databases")
def list_databases():
    return {"active": _active_db_name, "databases": sorted(_db_registry.keys())}


@app.post("/create_database")
async def create_database(payload: Dict[str, Any]):
    global _active_db_name
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Provide database name")
    if name in _db_registry:
        raise HTTPException(status_code=400, detail="Database already exists")
    _db_registry[name] = Database(name=name)
    _active_db_name = name
    return {"status": "ok", "active": _active_db_name}


@app.post("/switch_database")
async def switch_database(payload: Dict[str, Any]):
    global _active_db_name
    name = payload.get("name")
    if not name or name not in _db_registry:
        raise HTTPException(status_code=400, detail="Unknown database")
    _active_db_name = name
    return {"status": "ok", "active": _active_db_name}


# Existing table APIs bound to active DB
@app.post("/create_table")
async def create_table(payload: Dict[str, Any]):
    name = payload.get("name")
    schema = payload.get("schema")
    if not name or not isinstance(schema, list):
        raise HTTPException(status_code=400, detail="Invalid payload")
    try:
        table = get_db().create_table(name, schema)
        return {"status": "ok", "table": table.to_json()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/insert_row")
async def insert_row(payload: Dict[str, Any]):
    table = payload.get("table")
    values = payload.get("values")
    if not table or not isinstance(values, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    try:
        get_db().insert_row(table, values)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/tables")
def list_tables():
    db = get_db()
    return {
        "tables": [
            {
                "name": t.name,
                "columns": [{"name": c.name, "type": c.type_name} for c in t.columns],
                "rowCount": len(t.rows),
                "rows": [r.values for r in t.rows],
            }
            for t in db.tables.values()
        ]
    }


@app.get("/view_table/{name}")
def view_table(name: str):
    try:
        t = get_db().get_table(name)
        return t.to_json()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/delete_table")
async def delete_table(payload: Dict[str, Any]):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Provide table name")
    try:
        get_db().drop_table(name)
        return {"status": "deleted", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/union")
async def union_tables_endpoint(payload: Dict[str, Any]):
    from ..core.operations import union_tables

    left = payload.get("left")
    right = payload.get("right")
    requested = payload.get("name")
    if not left or not right:
        raise HTTPException(status_code=400, detail="Provide left and right table names")
    try:
        db = get_db()
        t1 = db.get_table(left)
        t2 = db.get_table(right)
        res = union_tables(t1, t2)
        # Preferred base name from client or default
        base = (requested or f"{t1.name}_UNION_{t2.name}").strip()
        # Cap to reasonable length
        if len(base) > 60:
            base = base[:60]
        name = base
        i = 1
        while name in db.tables:
            i += 1
            suffix = f"_{i}"
            max_base = 60 - len(suffix)
            name = (base[:max_base] if len(base) > max_base else base) + suffix
        res.name = name
        db.tables[name] = res
        return res.to_json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Persistence (local)
@app.post("/save")
async def save_db(payload: Dict[str, Any]):
    name = payload.get("name") or _active_db_name
    path = payload.get("path")
    try:
        db = _db_registry[name]
        target = Path(path) if path else BASE_DIR / f"../../{name}.json"
        db.save(str(target))
        return {"status": "ok", "path": str(target), "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/load")
async def load_db(payload: Dict[str, Any]):
    global _active_db_name
    name = payload.get("name")
    path = payload.get("path")
    if not name:
        raise HTTPException(status_code=400, detail="Provide database name")
    try:
        target = Path(path) if path else BASE_DIR / f"../../{name}.json"
        _db_registry[name] = Database.load(str(target))
        _active_db_name = name
        return {"status": "ok", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Google Drive integration (service account)

def _get_drive_service(scopes: List[str] | None = None):
    if service_account is None or build is None:
        raise RuntimeError("Google API client not installed")
    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    info = os.getenv("GOOGLE_SERVICE_ACCOUNT_INFO")
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if info:
        creds = service_account.Credentials.from_service_account_info(json.loads(info), scopes=scopes)
    elif file_path:
        creds = service_account.Credentials.from_service_account_file(file_path, scopes=scopes)
    else:
        raise RuntimeError("Provide GOOGLE_SERVICE_ACCOUNT_INFO or GOOGLE_SERVICE_ACCOUNT_FILE")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


@app.post("/save_drive")
async def save_drive(payload: Dict[str, Any]):
    name = payload.get("name") or _active_db_name
    folder_id = payload.get("folder_id")
    try:
        db = _db_registry[name]
        content = json.dumps(db.to_json(), ensure_ascii=False).encode("utf-8")
        drive = _get_drive_service(["https://www.googleapis.com/auth/drive.file"])
        media = MediaInMemoryUpload(body=content, mimetype="application/json", resumable=False)
        body: Dict[str, Any] = {"name": f"{name}.json"}
        if folder_id:
            body["parents"] = [folder_id]
        file = drive.files().create(body=body, media_body=media, fields="id").execute()
        return {"status": "ok", "file_id": file.get("id")}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/load_drive")
async def load_drive(payload: Dict[str, Any]):
    global _active_db_name
    name = payload.get("name")
    file_id = payload.get("file_id")
    if not name or not file_id:
        raise HTTPException(status_code=400, detail="Provide name and file_id")
    try:
        drive = _get_drive_service(["https://www.googleapis.com/auth/drive.readonly"])
        request = drive.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        data = json.loads(fh.read().decode("utf-8"))
        _db_registry[name] = Database.from_json(data)
        _active_db_name = name
        return {"status": "ok", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


