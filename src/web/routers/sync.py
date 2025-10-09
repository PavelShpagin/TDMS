from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..config import get_settings
from ..dependencies import AppState, get_app_state
from src.services.drive_service import DriveService


router = APIRouter(prefix="/api/databases", tags=["sync"])


@router.post("/{db_name}/sync/start")
async def start_sync(db_name: str, state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    if db_name not in state.db_registry:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Sync start failed: Database '{db_name}' not in registry. Available: {list(state.db_registry.keys())}")
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")

    settings = get_settings()

    try:
        import redis
        from uuid import uuid4
        from src.tasks.sync_tasks import sync_loop

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        # Require explicit user authentication for sync start (frontend will
        # prompt and save access token, then retry automatically).
        access_token = r.get("tdms:google:access_token")
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated with Google Drive. Please authenticate first."
            )
        
        token = str(uuid4())
        r.set(f"tdms:sync:token:{db_name}", token)
        sync_loop.delay(db_name, token)
        return {"status": "enabled", "database": db_name, "mode": "worker"}
    except HTTPException:
        # Re-raise HTTP exceptions (like auth errors) to be handled by FastAPI
        raise
    except Exception:
        # Desktop/local fallback (Redis/Celery not available)
        interval = 5

        if not hasattr(start_sync, "_local_sync_flags"):
            setattr(start_sync, "_local_sync_flags", {})  # type: ignore[attr-defined]

        stop_flag = threading.Event()
        getattr(start_sync, "_local_sync_flags")[db_name] = stop_flag  # type: ignore[index]

        def _local_sync_loop() -> None:
            access_token: Optional[str] = None
            while not stop_flag.is_set():
                try:
                    # Prefer Redis token
                    try:
                        import redis as redis_local

                        rr = redis_local.Redis.from_url(settings.redis_url, decode_responses=True)
                        rr.ping()
                        token_val = rr.get("tdms:google:access_token")
                        access_token = str(token_val) if token_val else None
                    except Exception:
                        pass

                    if not access_token:
                        stop_flag.wait(interval)
                        continue

                    db = state.db_registry.get(db_name)
                    if not db:
                        stop_flag.wait(interval)
                        continue

                    service = DriveService(access_token=access_token)
                    service.upload_or_update(db_name, db.to_json())
                except Exception:
                    pass
                finally:
                    stop_flag.wait(interval)

        t = threading.Thread(target=_local_sync_loop, daemon=True)
        t.start()
        return {"status": "enabled", "database": db_name, "mode": "local"}


@router.post("/{db_name}/sync/stop")
async def stop_sync(db_name: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        r.delete(f"tdms:sync:token:{db_name}")
        r.delete(f"tdms:sync:lock:{db_name}")
        return {"status": "disabled", "database": db_name}
    except Exception:
        try:
            stop_flags = getattr(start_sync, "_local_sync_flags", {})
            flag = stop_flags.get(db_name)
            if flag:
                flag.set()
                stop_flags.pop(db_name, None)
        except Exception:
            pass
        return {"status": "disabled", "database": db_name, "mode": "local"}


@router.get("/{db_name}/sync/status")
async def sync_status(db_name: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        token = r.get(f"tdms:sync:token:{db_name}")
        last = r.get(f"tdms:sync:last_sync:{db_name}")
        last_ts = float(last) if last else None  # type: ignore[arg-type]
        import time as _t

        last_human = _t.strftime('%Y-%m-%d %H:%M:%S', _t.localtime(last_ts)) if last_ts else None
        return {"database": db_name, "sync_enabled": bool(token), "mode": "worker", "last_sync_timestamp": last_ts, "last_sync_human": last_human}
    except Exception:
        try:
            stop_flags = getattr(start_sync, "_local_sync_flags", {})
            flag = stop_flags.get(db_name)
            local_running = bool(flag) and (not flag.is_set())  # type: ignore[union-attr]
            return {"database": db_name, "sync_enabled": local_running, "mode": "local"}
        except Exception:
            return {"database": db_name, "sync_enabled": False, "mode": "local"}


