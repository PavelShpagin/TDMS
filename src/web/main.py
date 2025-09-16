from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.database import Database


app = FastAPI(title="Table Database")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

db = Database(name="default")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    context = {"request": request, "tables": [t.to_json() for t in db.tables.values()]}
    return templates.TemplateResponse("index.html", context)


@app.post("/create_table")
async def create_table(payload: Dict[str, Any]):
    name = payload.get("name")
    schema = payload.get("schema")
    if not name or not isinstance(schema, list):
        raise HTTPException(status_code=400, detail="Invalid payload")
    try:
        table = db.create_table(name, schema)
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
        db.insert_row(table, values)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/tables")
def list_tables():
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
        t = db.get_table(name)
        return t.to_json()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/delete_table")
async def delete_table(payload: Dict[str, Any]):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Provide table name")
    try:
        db.drop_table(name)
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


@app.post("/save")
async def save_db(payload: Dict[str, Any]):
    path = payload.get("path", str(BASE_DIR / "../../database.json"))
    try:
        db.save(path)
        return {"status": "ok", "path": path}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/load")
async def load_db(payload: Dict[str, Any]):
    path = payload.get("path", str(BASE_DIR / "../../database.json"))
    try:
        global db
        db = Database.load(path)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


