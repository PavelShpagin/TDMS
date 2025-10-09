from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..schemas import GoogleTokenSaveRequest, GoogleAccessTokenRequest
from ..dependencies import AppState, get_app_state


router = APIRouter(prefix="/api/google", tags=["google"])


@router.get("/oauth/status")
async def google_auth_status() -> Dict[str, bool]:
    # Report whether Drive is configured and whether an access token is present in Redis
    configured = _is_drive_configured()
    authenticated = False
    try:
        import redis
        settings = get_settings()
        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        authenticated = bool(r.get("tdms:google:access_token"))
    except Exception:
        authenticated = False
    return {"configured": configured, "authenticated": authenticated}


@router.post("/oauth/save_token")
async def save_google_token(payload: GoogleTokenSaveRequest) -> Dict[str, Any]:
    try:
        from google_auth_oauthlib.flow import Flow

        refresh_token = payload.refresh_token
        code = payload.code
        if not refresh_token and not code:
            raise HTTPException(status_code=400, detail="Either refresh_token or code must be provided")

        client_secrets_dir = Path("secrets")
        client_secret_files = list(client_secrets_dir.glob("client_secret_*.json"))
        if not client_secret_files:
            raise HTTPException(status_code=500, detail="No client_secret file found in secrets/")

        if code:
            flow = Flow.from_client_secrets_file(
                str(client_secret_files[0]),
                scopes=["https://www.googleapis.com/auth/drive.file"],
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
            token_data = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }
        else:
            with open(client_secret_files[0]) as f:
                client_config = json.load(f)
                if "installed" in client_config:
                    client_info = client_config["installed"]
                elif "web" in client_config:
                    client_info = client_config["web"]
                else:
                    raise HTTPException(status_code=500, detail="Invalid client_secret format")
            token_data = {
                "refresh_token": refresh_token,
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": client_info["client_id"],
                "client_secret": client_info["client_secret"],
                "scopes": ["https://www.googleapis.com/auth/drive.file"],
            }

        token_path = Path("secrets/token.json")
        with open(token_path, "w") as f:
            json.dump(token_data, f, indent=2)
        return {"status": "ok", "message": "Google Drive credentials saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/save_access_token")
async def save_access_token(payload: GoogleAccessTokenRequest) -> Dict[str, Any]:
    import time
    settings = get_settings()
    try:
        token = payload.access_token
        expires_in = payload.expires_in
        if not token:
            raise HTTPException(status_code=400, detail="Missing access_token")
        try:
            import redis

            r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            r.ping()
            r.set("tdms:google:access_token", token)
            if expires_in:
                try:
                    ttl = max(1, int(expires_in) - 30)
                    r.expire("tdms:google:access_token", ttl)
                    r.set("tdms:google:token_expiry", str(int(time.time()) + ttl))
                except Exception:
                    pass
        except Exception:
            # In desktop fallback we keep token in memory via sync loop
            pass
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save_drive")
async def save_drive(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.get("name") or state.active_db_name
    folder_id = payload.get("folder_id") or get_settings().drive_folder_id
    if name not in state.db_registry:
        raise HTTPException(status_code=404, detail="Database not found")
    try:
        db = state.db_registry[name]
        content = json.dumps(db.to_json(), ensure_ascii=False).encode("utf-8")
        drive = _get_drive_service(["https://www.googleapis.com/auth/drive.file"])
        body: Dict[str, Any] = {"name": f"{name}.json"}
        if folder_id:
            body["parents"] = [folder_id]
        else:
            raise HTTPException(status_code=400, detail="Provide a shared drive folder_id (or set DRIVE_FOLDER_ID env)")
        from googleapiclient.http import MediaInMemoryUpload  # type: ignore

        media = MediaInMemoryUpload(body=content, mimetype="application/json", resumable=False)  # type: ignore[arg-type]
        file = drive.files().create(body=body, media_body=media, fields="id", supportsAllDrives=True).execute()
        return {"status": "ok", "file_id": file.get("id")}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/load_drive")
async def load_drive(payload: Dict[str, Any], state: AppState = Depends(get_app_state)) -> Dict[str, Any]:
    name = payload.get("name")
    file_id = payload.get("file_id")
    if not name or not file_id:
        raise HTTPException(status_code=400, detail="Provide name and file_id")
    try:
        drive = _get_drive_service(["https://www.googleapis.com/auth/drive.readonly"])
        request = drive.files().get_media(fileId=file_id)
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        data = json.loads(fh.read().decode("utf-8"))
        state.db_registry[name] = Database.from_json(data)  # type: ignore[name-defined]
        state.active_db_name = name
        return {"status": "ok", "name": name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/drive_files")
async def list_drive_files() -> Dict[str, Any]:
    try:
        drive = _get_drive_service(["https://www.googleapis.com/auth/drive.readonly"])
        files: List[Dict[str, Any]] = []
        page_token = None
        while True:
            resp = (
                drive.files()
                .list(
                    q="mimeType='application/json'",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                    orderBy="modifiedTime desc",
                    pageToken=page_token,
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    corpora="allDrives",
                )
                .execute()
            )
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return {"files": files}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---- Helpers (local to router) ----

def _get_drive_service(scopes: List[str] | None = None):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Google API client not installed") from exc

    scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
    settings = get_settings()

    info = settings.google_service_account_info
    file_path = settings.google_service_account_file
    if info:
        creds = service_account.Credentials.from_service_account_info(json.loads(info), scopes=scopes)  # type: ignore[arg-type]
    elif file_path:
        p = Path(file_path)
        if not p.exists():
            candidates = [
                Path.cwd() / file_path,
                Path.cwd() / "secrets" / file_path,
                Path(__file__).resolve().parents[2] / file_path,
                Path(__file__).resolve().parents[2] / "secrets" / file_path,
            ]
            for c in candidates:
                if c.exists():
                    p = c
                    break
        creds = service_account.Credentials.from_service_account_file(str(p), scopes=scopes)  # type: ignore[arg-type]
    else:
        # Fallback autodetect
        try:
            root = Path.cwd()
            secrets_dir = root / "secrets"
            candidates = list(root.glob("*.json")) + list(Path(__file__).resolve().parents[2].glob("*.json"))
            if secrets_dir.exists():
                candidates += list(secrets_dir.glob("*.json"))
            gp_secrets = Path(__file__).resolve().parents[2] / "secrets"
            if gp_secrets.exists():
                candidates += list(gp_secrets.glob("*.json"))
            for candidate in candidates:
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    if data.get("type") == "service_account" and "client_email" in data and "private_key" in data:
                        creds = service_account.Credentials.from_service_account_file(str(candidate), scopes=scopes)  # type: ignore[arg-type]
                        break
                except Exception:
                    continue
            else:
                raise RuntimeError("Provide GOOGLE_SERVICE_ACCOUNT_INFO or GOOGLE_SERVICE_ACCOUNT_FILE")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Provide GOOGLE_SERVICE_ACCOUNT_INFO or GOOGLE_SERVICE_ACCOUNT_FILE") from exc
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _is_drive_configured() -> bool:
    """Return True if Drive access is configured for uploads."""
    settings = get_settings()
    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        if r.get("tdms:google:access_token"):
            return True
    except Exception:
        pass
    try:
        _ = _get_drive_service(["https://www.googleapis.com/auth/drive.file"])  # noqa: F841
        return True
    except Exception:
        return False


