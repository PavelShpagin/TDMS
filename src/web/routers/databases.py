from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.core.database import Database
from ..dependencies import AppState, get_app_state
from ..schemas import CreateDatabaseRequest, SwitchOrDeleteDatabaseRequest, RenameDatabaseRequest


router = APIRouter(prefix="", tags=["databases"])


@router.get("/databases")
async def list_databases(state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    import time
    names = list(state.db_registry.keys())

    def get_mtime(name: str) -> float:
        try:
            path = state.get_db_file_path(name)
            return path.stat().st_mtime if path.exists() else time.time()
        except Exception:
            return 0.0

    return {"active": state.active_db_name, "databases": sorted(names, key=get_mtime, reverse=True)}


@router.post("/databases", status_code=201)
async def create_database(payload: CreateDatabaseRequest, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.name
    if not name:
        raise HTTPException(status_code=400, detail="Provide database name")
    if name in state.db_registry:
        raise HTTPException(status_code=400, detail="Database already exists")
    state.db_registry[name] = state.load_or_create_database(name)
    state.active_db_name = name
    state.save_database(name)
    return {"status": "ok", "active": state.active_db_name}


@router.put("/databases/{name}")
async def switch_database(name: str, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    if name not in state.db_registry:
        state.db_registry[name] = state.load_or_create_database(name)
    state.active_db_name = name
    return {"status": "ok", "active": state.active_db_name}


@router.delete("/databases/{name}")
async def delete_database(name: str, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    if name not in state.db_registry:
        raise HTTPException(status_code=404, detail="Database not found")
    if name == "default" and len(state.db_registry) == 1:
        raise HTTPException(status_code=400, detail="Cannot delete default database")

    state.db_registry.pop(name, None)

    try:
        path = state.get_db_file_path(name)
        if path.exists():
            path.unlink()
    except Exception:
        pass

    # If deleted active, select another or recreate default
    if state.active_db_name == name:
        if state.db_registry:
            state.active_db_name = sorted(state.db_registry.keys())[0]
        else:
            state.db_registry["default"] = Database(name="default")
            state.active_db_name = "default"

    # Best-effort Redis cleanup for sync state
    try:
        from ..config import get_settings
        import redis
        settings = get_settings()
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.delete(f"tdms:sync:token:{name}")
        r.delete(f"tdms:sync:lock:{name}")
        r.delete(f"tdms:sync:last_sync:{name}")
    except Exception:
        pass

    return {"status": "ok", "active": state.active_db_name}


@router.put("/databases/{old}/rename/{new}")
async def rename_database(old: str, new: str, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    if not new:
        raise HTTPException(status_code=400, detail="Provide new database name")
    if old not in state.db_registry:
        raise HTTPException(status_code=404, detail="Database not found")
    if new in state.db_registry and new != old:
        raise HTTPException(status_code=400, detail="Target name already exists")
    db = state.db_registry.pop(old)
    db.name = new
    state.db_registry[new] = db

    # Rename file on disk
    try:
        old_file = state.get_db_file_path(old)
        new_file = state.get_db_file_path(new)
        if old_file.exists():
            old_file.rename(new_file)
    except Exception:
        pass

    # Migrate sync state (if any)
    try:
        from ..config import get_settings
        import redis
        from uuid import uuid4

        settings = get_settings()
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        old_token_key = f"tdms:sync:token:{old}"
        old_lock_key = f"tdms:sync:lock:{old}"
        old_last_key = f"tdms:sync:last_sync:{old}"
        token = r.get(old_token_key)
        if token:
            r.delete(old_token_key)
            r.delete(old_lock_key)
            last_sync = r.get(old_last_key)
            if last_sync:
                r.set(f"tdms:sync:last_sync:{new}", last_sync)  # type: ignore[arg-type]
                r.delete(old_last_key)
            new_token = str(uuid4())
            r.set(f"tdms:sync:token:{new}", new_token)  # type: ignore[arg-type]
            from src.tasks.sync_tasks import sync_loop
            sync_loop.delay(new, new_token)
    except Exception:
        pass

    if state.active_db_name == old:
        state.active_db_name = new
    return {"status": "ok", "active": state.active_db_name}


# ---- Backward-compatible endpoints ----

@router.post("/create_database")
async def create_database_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = CreateDatabaseRequest.model_validate(payload)
    return await create_database(model, state)  # type: ignore[arg-type]


@router.post("/switch_database")
async def switch_database_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = SwitchOrDeleteDatabaseRequest.model_validate(payload)
    return await switch_database(model.name, state)


@router.post("/delete_database")
async def delete_database_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Delete database compat called with payload: {payload}")
    try:
        model = SwitchOrDeleteDatabaseRequest.model_validate(payload)
        logger.info(f"Validated model, deleting database: {model.name}")
        return await delete_database(model.name, state)
    except Exception as e:
        logger.error(f"Delete database compat failed: {e}")
        raise


@router.post("/rename_database")
async def rename_database_compat(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = RenameDatabaseRequest.model_validate(payload)
    old = model.old or state.active_db_name
    return await rename_database(old, model.new, state)


