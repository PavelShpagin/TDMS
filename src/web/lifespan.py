from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI

from .config import get_settings
from .dependencies import AppState


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager (startup/shutdown replacement).

    - Loads databases from disk on startup
    - Saves databases and cleans up external resources on shutdown
    """
    settings = get_settings()

    # Attach app-wide state container (shared where DI is not present)
    storage_dir = Path(settings.db_storage_dir)
    storage_dir.mkdir(exist_ok=True)
    app.state.app_state = AppState(storage_dir)

    # Load existing databases
    try:
        for db_file in storage_dir.glob("*.json"):
            db_name = db_file.stem
            if db_name not in app.state.app_state.db_registry:
                try:
                    app.state.app_state.db_registry[db_name] = app.state.app_state.load_or_create_database(db_name)
                except Exception:
                    pass
    except Exception:
        pass

    # Proactively cleanup Redis tokens/locks on startup as well, in case the
    # previous shutdown was ungraceful and the 'finally' block didn't run.
    try:
        import redis  # type: ignore

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        # OAuth tokens
        try:
            r.delete("tdms:google:access_token")
            r.delete("tdms:google:token_expiry")
        except Exception:
            pass
        # Sync tokens/locks
        try:
            for key in r.scan_iter("tdms:sync:token:*"):
                r.delete(key)
            for key in r.scan_iter("tdms:sync:lock:*"):
                r.delete(key)
        except Exception:
            pass
    except Exception:
        # Redis may be unavailable on startup; ignore
        pass

    try:
        yield
    finally:
        # Persist databases
        try:
            for name in list(app.state.app_state.db_registry.keys()):
                try:
                    app.state.app_state.save_database(name)
                except Exception:
                    pass
        except Exception:
            pass

        # Cleanup Redis: Delete all auth and sync tokens for clean restart
        try:
            import redis

            r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            
            # Delete OAuth tokens (user will re-authenticate on next use)
            r.delete("tdms:google:access_token")
            r.delete("tdms:google:token_expiry")
            
            # Delete all sync session tokens (stop all active sync loops)
            for key in r.scan_iter("tdms:sync:token:*"):
                r.delete(key)
            
            # Delete all sync locks (cleanup)
            for key in r.scan_iter("tdms:sync:lock:*"):
                r.delete(key)
            
            # Note: Celery task queue and results remain in Redis for worker recovery
        except Exception:
            pass


