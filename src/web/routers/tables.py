from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.core.database import Database
from ..dependencies import AppState, get_active_db, get_app_state
from ..schemas import CreateTableRequest, InsertRowRequest, UpdateRowRequest


router = APIRouter(prefix="", tags=["tables"])


@router.post("/tables", status_code=201)
async def create_table(payload: CreateTableRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.name
    schema = [{"name": c.name, "type": c.type} for c in payload.columns]
    try:
        db = state.db_registry[state.active_db_name]
        table = db.create_table(name, schema)
        # Save to disk immediately for sync to pick up changes
        state.save_database(state.active_db_name)
        return {"status": "ok", "table": table.to_json()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/tables/{table}/rows", status_code=201)
async def insert_row(table: str, payload: InsertRowRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    values = payload.values
    try:
        db = state.db_registry[state.active_db_name]
        db.insert_row(table, values)
        # Save to disk immediately for sync to pick up changes
        state.save_database(state.active_db_name)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/tables/{table}/rows/{row_index}")
async def delete_row(table: str, row_index: int, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    try:
        db = state.db_registry[state.active_db_name]
        table_obj = db.tables[table]
        if row_index < 0 or row_index >= len(table_obj.rows):
            raise HTTPException(status_code=400, detail="Invalid row index")
        table_obj.rows.pop(row_index)
        # Save to disk immediately for sync to pick up changes
        state.save_database(state.active_db_name)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/tables/{table}/rows/{row_index}")
async def update_row(table: str, row_index: int, payload: UpdateRowRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    values = payload.values
    try:
        db = state.db_registry[state.active_db_name]
        table_obj = db.tables[table]
        if row_index < 0 or row_index >= len(table_obj.rows):
            raise HTTPException(status_code=400, detail="Invalid row index")
        db.edit_row(table, int(row_index), values)
        # Save to disk immediately for sync to pick up changes
        state.save_database(state.active_db_name)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tables")
async def list_tables(db: Database = Depends(get_active_db)) -> Dict[str, Any]:
    return {
        "tables": [
            {
                "name": t.name,
                "columns": [{"name": c.name, "type": c.type_name} for c in t.columns],
                "rowCount": len(t.rows),
                "rows": [r.values if hasattr(r, "values") else (dict(r) if isinstance(r, dict) else r) for r in t.rows],
            }
            for t in db.tables.values()
        ]
    }


@router.get("/tables/{name}")
async def view_table(name: str, db: Database = Depends(get_active_db)) -> Dict[str, Any]:
    try:
        t = db.get_table(name)
        return t.to_json()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/tables/{name}")
async def delete_table(name: str, db: Database = Depends(get_active_db), state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    try:
        db.drop_table(name)
        # Save to disk immediately for sync to pick up changes
        state.save_database(state.active_db_name)
        return {"status": "deleted", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---- Backward-compatible endpoints ----

@router.post("/create_table")
async def create_table_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = CreateTableRequest.model_validate(payload)
    return await create_table(model, state)


@router.post("/insert_row")
async def insert_row_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    table = payload.get("table")
    values = payload.get("values")
    if not table or not isinstance(values, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    return await insert_row(table, InsertRowRequest(values=values), state)


@router.post("/delete_row")
async def delete_row_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    table = payload.get("table")
    row_index = payload.get("row_index")
    if not table or row_index is None:
        raise HTTPException(status_code=400, detail="Provide table and row_index")
    return await delete_row(table, int(row_index), state)


@router.post("/update_row")
async def update_row_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    table = payload.get("table")
    row_index = payload.get("row_index")
    values = payload.get("values")
    if not table or row_index is None or values is None:
        raise HTTPException(status_code=400, detail="Provide table, row_index, and values")
    return await update_row(table, int(row_index), UpdateRowRequest(values=values), state)


@router.post("/delete_table")
async def delete_table_compat(payload: Dict[str, Any], db: Database = Depends(get_active_db), state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Provide table name")
    return await delete_table(name, db, state)


@router.get("/view_table/{name}")
async def view_table_compat(name: str, db: Database = Depends(get_active_db)) -> Dict[str, Any]:
    return await view_table(name, db)


