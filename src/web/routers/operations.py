from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_active_db, AppState, get_app_state
from ..schemas import UnionRequest


router = APIRouter(prefix="", tags=["operations"])


@router.post("/tables/union", status_code=201)
async def union_tables(payload: UnionRequest, db=Depends(get_active_db), state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    from src.core.operations import union_tables as _union

    left = payload.left
    right = payload.right
    requested = payload.name
    if not left or not right:
        raise HTTPException(status_code=400, detail="Provide left and right table names")
    try:
        t1 = db.get_table(left)
        t2 = db.get_table(right)
        res = _union(t1, t2)
        base = (requested or f"{t1.name}_UNION_{t2.name}").strip()
        if len(base) > 60:
            base = base[:60]
        name = base
        counter = 1
        while name in db.tables:
            suffix = f" ({counter})"
            max_base = 60 - len(suffix)
            name = (base[:max_base] if len(base) > max_base else base) + suffix
            counter += 1
        res.name = name
        db.tables[name] = res
        # Persist immediately so Celery sync sees it and users don't lose data
        try:
            state.save_database(state.active_db_name)
        except Exception:
            # Non-fatal; still return result
            pass
        return res.to_json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# Backward compatibility: original /union endpoint
@router.post("/union")
async def union_tables_compat(payload: Dict[str, Any], db=Depends(get_active_db), state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    model = UnionRequest.model_validate(payload)
    return await union_tables(model, db, state)  # type: ignore[arg-type]


