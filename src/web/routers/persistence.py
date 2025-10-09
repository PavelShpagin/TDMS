from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, get_app_state
from ..schemas import SaveRequest, LoadRequest, ExportQuery, ImportDatabaseRequest


router = APIRouter(prefix="", tags=["persistence"])


@router.put("/save")
async def save_db(payload: SaveRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.name or state.active_db_name
    path = payload.path
    try:
        db = state.db_registry[name]
        target = Path(path) if path else Path(__file__).resolve().parent / f"../../{name}.json"
        db.save(str(target))
        return {"status": "ok", "path": str(target), "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/load")
async def load_db(payload: LoadRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.name
    path = payload.path
    try:
        target = Path(path) if path else Path(__file__).resolve().parent / f"../../{name}.json"
        state.db_registry[name] = state.load_or_create_database(name)
        state.db_registry[name] = state.db_registry[name].load(str(target))  # type: ignore[attr-defined]
        state.active_db_name = name
        return {"status": "ok", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/export")
async def export_db(name: str | None = None, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    target_name = name or state.active_db_name
    if target_name not in state.db_registry:
        raise HTTPException(status_code=404, detail="Database not found")
    try:
        db = state.db_registry[target_name]
        return db.to_json()  # type: ignore[return-value]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/import_database")
async def import_database(payload: ImportDatabaseRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.name
    data = payload.data
    try:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON data format")
        elif not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Data must be JSON object or string")

        original_name = name
        counter = 1
        while name in state.db_registry:
            name = f"{original_name} ({counter})"
            counter += 1

        from src.core.database import Database

        db = Database.from_json(data)  # type: ignore[arg-type]
        db.name = name
        state.db_registry[name] = db
        state.active_db_name = name
        # Auto-save to disk
        try:
            db.save(str(state.get_db_file_path(name)))
        except Exception:
            pass
        return {"status": "ok", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---- Backward-compatible endpoints ----

@router.post("/save")
async def save_db_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = SaveRequest.model_validate(payload)
    return await save_db(model, state)


@router.post("/export")
async def export_db_compat(payload: Dict[str, Any] | None = None, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.get("name") if isinstance(payload, dict) else None
    return await export_db(name, state)  # type: ignore[arg-type]


