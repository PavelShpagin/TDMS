import json
from pathlib import Path
from src.tasks.celery_app import celery_app, get_redis_client
from src.services.drive_service import DriveService


@celery_app.task(name="tdms.sync_loop", bind=True, max_retries=3)
def sync_loop(self, db_name: str, token: str, interval: int = 5):
    """Background task that syncs database to Google Drive every interval seconds.
    
    Uses shared Redis connection pool via get_redis_client() for efficiency.
    Self-reschedules with countdown=interval for continuous sync.
    """
    r = get_redis_client()

    current_token = r.get(f"tdms:sync:token:{db_name}")
    if not current_token or current_token != token:
        return {"status": "stopped", "reason": "token_invalid", "db": db_name}

    lock_key = f"tdms:sync:lock:{db_name}"
    if not r.set(lock_key, "1", nx=True, ex=interval * 2):
        sync_loop.apply_async(args=[db_name, token, interval], countdown=interval)
        return {"status": "locked", "db": db_name, "rescheduled": True}

    try:
        db_path = Path(f"databases/{db_name}.json")
        if not db_path.exists():
            sync_loop.apply_async(args=[db_name, token, interval], countdown=interval)
            return {"status": "file_missing", "db": db_name, "rescheduled": True}

        # Always sync on every interval - don't rely on mtime since FastAPI
        # modifies _db_registry in memory and may not write to disk immediately
        with db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        try:
            # Try to get access token from Redis first
            access_token_val = r.get("tdms:google:access_token")
            access_token = str(access_token_val) if access_token_val else None
            drive_service = DriveService(access_token=access_token)
            fid = drive_service.upload_or_update(db_name, data)
            status = "synced"
        except FileNotFoundError:
            # Credentials not configured; skip upload but keep loop alive
            status = "drive_not_configured"

        sync_loop.apply_async(args=[db_name, token, interval], countdown=interval)
        return {"status": status, "db": db_name, "rescheduled": True, "next_in": interval}
    except Exception as e:
        retry_delay = interval * (self.request.retries + 1)
        sync_loop.apply_async(args=[db_name, token, interval], countdown=retry_delay)
        raise
    finally:
        r.delete(lock_key)


