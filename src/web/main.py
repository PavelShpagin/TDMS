from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.database import Database

import json
import os
import io
import re
import time

# Load environment from .env if present
try:
	from dotenv import load_dotenv  # type: ignore
	# Try project root and this module's grandparent
	load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
	load_dotenv(dotenv_path=(Path(__file__).resolve().parents[2] / ".env"), override=False)
except Exception:
	pass

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

# In-memory OAuth state store for desktop loopback flow
_oauth_states: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Load existing databases on startup"""
    global _db_registry
    if DB_STORAGE_DIR.exists():
        for db_file in DB_STORAGE_DIR.glob("*.json"):
            db_name = db_file.stem
            if db_name not in _db_registry:
                try:
                    _db_registry[db_name] = Database.load(str(db_file))
                    print(f"Loaded database: {db_name}")
                except Exception as e:
                    print(f"Warning: Could not load database {db_name}: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Save all databases on shutdown"""
    print("Saving all databases...")
    for db_name in _db_registry:
        _save_database(db_name)
		
    print("All databases saved.")

# Multi-database registry with persistence
_db_registry: Dict[str, Database] = {}
_active_db_name: str = "default"

# Database persistence settings
DB_STORAGE_DIR = Path("databases")
DB_STORAGE_DIR.mkdir(exist_ok=True)

def _get_db_file_path(db_name: str) -> Path:
    """Get the file path for a database"""
    return DB_STORAGE_DIR / f"{db_name}.json"

def _load_or_create_database(db_name: str) -> Database:
    """Load database from file or create new one"""
    db_file = _get_db_file_path(db_name)
    if db_file.exists():
        try:
            return Database.load(str(db_file))
        except Exception as e:
            print(f"Warning: Could not load database {db_name}: {e}")
            print(f"Creating new database instead.")
    return Database(name=db_name)

def _save_database(db_name: str) -> None:
    """Save database to file"""
    if db_name in _db_registry:
        try:
            db_file = _get_db_file_path(db_name)
            _db_registry[db_name].save(str(db_file))
        except Exception as e:
            print(f"Warning: Could not save database {db_name}: {e}")

def _auto_save_active_db() -> None:
    """Automatically save the active database"""
    _save_database(_active_db_name)

# Initialize default database with persistence
_db_registry[_active_db_name] = _load_or_create_database(_active_db_name)


def get_db() -> Database:
	return _db_registry[_active_db_name]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Detect if this is desktop mode (check user agent and port)
    user_agent = request.headers.get("user-agent", "").lower()
    port = request.url.port
    is_desktop = (
        "pywebview" in user_agent or  # PyWebView user agent
        (port != 8000 and port is not None)  # Not standard web port
    )
    
    # Desktop detection based on port
    
    # Detect Google OAuth client id and secret (env first, then secrets/client_secret_*.json)
    if is_desktop:
        # For desktop mode, use DESKTOP_ prefixed variables first
        client_id = os.getenv("DESKTOP_GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("DESKTOP_GOOGLE_OAUTH_CLIENT_SECRET")
        # Desktop OAuth configuration loaded
    else:
        # For web mode, use regular variables
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        # Web OAuth configuration loaded
    
    if not client_id:  # Load Google config from JSON files as fallback
        try:
            root = Path.cwd()
            secrets_dir = root / "secrets"
            candidates: List[Path] = []
            candidates += list(root.glob("client_secret*.json"))
            candidates += list((BASE_DIR.parent.parent).glob("client_secret*.json"))
            candidates += list(secrets_dir.glob("client_secret*.json")) if secrets_dir.exists() else []
            gp_secrets = (BASE_DIR.parent.parent / "secrets")
            candidates += list(gp_secrets.glob("client_secret*.json")) if gp_secrets.exists() else []
            
            for f in candidates:
                data = json.loads(f.read_text(encoding="utf-8"))
                
                if is_desktop:
                    # For desktop, prioritize "installed" type credentials
                    if "installed" in data and "client_id" in data["installed"]:
                        client_id = data["installed"]["client_id"]
                        client_secret = data["installed"]["client_secret"]
                        print(f"Desktop using credentials from: {f.name}")
                        break
                else:
                    # For web, prioritize "web" type credentials
                    if "web" in data and "client_id" in data["web"]:
                        client_id = data["web"]["client_id"]
                        client_secret = data["web"]["client_secret"]
                        print(f"Web using credentials from: {f.name}")
                        break
                        
            # Fallback: if no matching type found, use any available
            if not client_id:
                for f in candidates:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if "web" in data and "client_id" in data["web"]:
                        client_id = data["web"]["client_id"]
                        client_secret = data["web"]["client_secret"]
                        break
                    elif "installed" in data and "client_id" in data["installed"]:
                        client_id = data["installed"]["client_id"]
                        client_secret = data["installed"]["client_secret"]
                        break
        except Exception as e:
            print(f"Error loading credentials: {e}")
            client_id = None
            client_secret = None
    
    context = {
        "request": request,
        "tables": [t.to_json() for t in get_db().tables.values()],
        "google_client_id": client_id or "",  # Enable Google for both web and desktop
        "google_client_secret": client_secret or "",  # Enable Google for both web and desktop
        "google_api_key": os.getenv("GOOGLE_API_KEY", "") if not is_desktop else "",
        "google_app_id": os.getenv("GOOGLE_PICKER_APP_ID", "") if not is_desktop else "",
        "google_refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN", "") if is_desktop else "",
        "is_desktop": is_desktop,
    }
    return templates.TemplateResponse("index.html", context)


# ---- Desktop OAuth (Loopback) helpers ----
@app.get("/oauth/callback")
def oauth_callback(request: Request):
    """Desktop loopback redirect target. Stores code by state and shows a tiny page."""
    try:
        params = dict(request.query_params)
        state = params.get("state")
        code = params.get("code")
        error = params.get("error")
        if state:
            _oauth_states[state] = {
                "code": code,
                "error": error,
            }
        # Minimal page that can be auto-closed by the user
        html = """
<!doctype html>
<html><head><meta charset=\"utf-8\"><title>Authentication complete</title></head>
<body style=\"font-family:system-ui,Segoe UI,Arial,sans-serif;\">
  <h3>Authentication complete</h3>
  <p>You can close this window and return to the app.</p>
</body></html>
"""
        return HTMLResponse(content=html)
    except Exception as exc:  # pragma: no cover
        return HTMLResponse(content=f"Error: {exc}", status_code=400)


@app.get("/oauth/poll")
def oauth_poll(state: str | None = None):
    """Client polls for an authorization code using the provided state."""
    if not state:
        return JSONResponse({"status": "error", "detail": "missing state"}, status_code=400)
    data = _oauth_states.get(state)
    if not data:
        return JSONResponse({"status": "pending"})
    # do not delete immediately to allow retries; the client may clear it after exchange
    return JSONResponse({"status": "ok", **data})


# Database management
@app.get("/databases")
def list_databases():
	# Sort databases by modification time (newest first)
	db_names = list(_db_registry.keys())
	
	def get_db_mtime(name):
		try:
			db_file_path = _get_db_file_path(name)
			if db_file_path.exists():
				return db_file_path.stat().st_mtime
			else:
				# If file doesn't exist, use current time (for new databases)
				return time.time()
		except:
			return 0
	
	sorted_names = sorted(db_names, key=get_db_mtime, reverse=True)
	return {"active": _active_db_name, "databases": sorted_names}


@app.post("/create_database")
async def create_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	if not name:
		raise HTTPException(status_code=400, detail="Provide database name")
	if name in _db_registry:
		raise HTTPException(status_code=400, detail="Database already exists")
	_db_registry[name] = _load_or_create_database(name)
	_active_db_name = name
	_auto_save_active_db()
	return {"status": "ok", "active": _active_db_name}


@app.post("/switch_database")
async def switch_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	if not name:
		raise HTTPException(status_code=400, detail="Provide database name")
	if name not in _db_registry:
		# Try to load database from file
		_db_registry[name] = _load_or_create_database(name)
	_active_db_name = name
	return {"status": "ok", "active": _active_db_name}


@app.post("/delete_database")
async def delete_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	if not name:
		raise HTTPException(status_code=400, detail="Provide database name")
	if name not in _db_registry:
		raise HTTPException(status_code=404, detail="Database not found")
	# Prevent deleting the reserved default if needed
	if name == "default" and len(_db_registry) == 1:
		raise HTTPException(status_code=400, detail="Cannot delete default database")
	
	# Remove from memory registry
	_db_registry.pop(name, None)
	
	# Delete the actual JSON file from disk
	try:
		db_file_path = _get_db_file_path(name)
		if db_file_path.exists():
			db_file_path.unlink()  # Delete the file
			print(f"Deleted database file: {db_file_path}")
	except Exception as e:
		print(f"Warning: Could not delete database file {name}: {e}")
		# Don't fail the request if file deletion fails
	
	if _active_db_name == name:
		if _db_registry:
			_active_db_name = sorted(_db_registry.keys())[0]
		else:
			# Recreate default if everything is deleted
			_db_registry["default"] = Database(name="default")
			_active_db_name = "default"
	return {"status": "ok", "active": _active_db_name}


@app.post("/rename_database")
async def rename_database(payload: Dict[str, Any]):
	global _active_db_name
	old = payload.get("old") or _active_db_name
	new = payload.get("new")
	if not new:
		raise HTTPException(status_code=400, detail="Provide new database name")
	if old not in _db_registry:
		raise HTTPException(status_code=404, detail="Database not found")
	if new in _db_registry and new != old:
		raise HTTPException(status_code=400, detail="Target name already exists")
	db = _db_registry.pop(old)
	db.name = new
	_db_registry[new] = db
	if _active_db_name == old:
		_active_db_name = new
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
		_auto_save_active_db()
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
		_auto_save_active_db()
		return {"status": "ok"}
	except Exception as exc:
		raise HTTPException(status_code=400, detail=str(exc))


@app.post("/delete_row")
async def delete_row(payload: Dict[str, Any]):
	table = payload.get("table")
	row_index = payload.get("row_index")
	if not table or row_index is None:
		raise HTTPException(status_code=400, detail="Provide table and row_index")
	try:
		table_obj = get_db().tables[table]
		if row_index < 0 or row_index >= len(table_obj.rows):
			raise HTTPException(status_code=400, detail="Invalid row index")
		
		# Remove the row at the specified index
		table_obj.rows.pop(row_index)
		_auto_save_active_db()
		return {"status": "ok"}
	except Exception as exc:
		raise HTTPException(status_code=400, detail=str(exc))


@app.post("/update_row")
async def update_row(payload: Dict[str, Any]):
	table = payload.get("table")
	row_index = payload.get("row_index")
	values = payload.get("values")
	if not table or row_index is None or not values:
		raise HTTPException(status_code=400, detail="Provide table, row_index, and values")
	try:
		table_obj = get_db().tables[table]
		if row_index < 0 or row_index >= len(table_obj.rows):
			raise HTTPException(status_code=400, detail="Invalid row index")
		
		# Update the row at the specified index
		table_obj.rows[row_index] = values
		_auto_save_active_db()
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
		_auto_save_active_db()
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
		_auto_save_active_db()
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


@app.post("/export")
async def export_db(payload: Dict[str, Any]):
	"""Export database to JSON format"""
	name = payload.get("name") or _active_db_name
	if name not in _db_registry:
		raise HTTPException(status_code=404, detail="Database not found")
	try:
		db = _db_registry[name]
		return db.to_json()
	except Exception as exc:
		raise HTTPException(status_code=400, detail=str(exc))


@app.post("/import_database")
async def import_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	data = payload.get("data")
	if not name or not data:
		raise HTTPException(status_code=400, detail="Provide name and data")
	
	try:
		# Handle both string and dict data
		if isinstance(data, str):
			try:
				data = json.loads(data)
			except json.JSONDecodeError:
				raise HTTPException(status_code=400, detail="Invalid JSON data format")
		elif not isinstance(data, dict):
			raise HTTPException(status_code=400, detail="Data must be JSON object or string")
		
		# Handle duplicate names by adding suffix (1), (2), etc.
		original_name = name
		counter = 1
		while name in _db_registry:
			name = f"{original_name} ({counter})"
			counter += 1
		
		db = Database.from_json(data)
		db.name = name
		_db_registry[name] = db
		_active_db_name = name
		_auto_save_active_db()  # Save to disk
		return {"status": "ok", "name": name}
	except Exception as exc:
		raise HTTPException(status_code=400, detail=str(exc))


# Google Drive integration (service account)

def _get_drive_service(scopes: List[str] | None = None):
	global service_account, build, MediaInMemoryUpload, MediaIoBaseDownload
	# Lazy import to handle post-install availability
	if service_account is None or build is None:
		try:
			from google.oauth2 import service_account as _sa  # type: ignore
			from googleapiclient.discovery import build as _build  # type: ignore
			from googleapiclient.http import (  # type: ignore
				MediaInMemoryUpload as _MediaInMemoryUpload,
				MediaIoBaseDownload as _MediaIoBaseDownload,
			)
			service_account = _sa
			build = _build
			MediaInMemoryUpload = _MediaInMemoryUpload
			MediaIoBaseDownload = _MediaIoBaseDownload
		except Exception as exc:  # pragma: no cover
			raise RuntimeError("Google API client not installed") from exc
	scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]
	info = os.getenv("GOOGLE_SERVICE_ACCOUNT_INFO")
	file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
	if info:
		creds = service_account.Credentials.from_service_account_info(json.loads(info), scopes=scopes)  # type: ignore[arg-type]
	elif file_path:
		p = Path(file_path)
		if not p.exists():
			# Try resolve against common secrets locations
			candidates = [
				Path.cwd() / file_path,
				Path.cwd() / "secrets" / file_path,
				(BASE_DIR.parent.parent) / file_path,
				(BASE_DIR.parent.parent) / "secrets" / file_path,
			]
			for c in candidates:
				if c.exists():
					p = c
					break
		creds = service_account.Credentials.from_service_account_file(str(p), scopes=scopes)  # type: ignore[arg-type]
	else:
		# Fallback: try to detect a service account JSON in project root and /secrets
		try:
			root = Path.cwd()
			secrets_dir = root / "secrets"
			candidates: List[Path] = []
			candidates += list(root.glob("*.json"))
			candidates += list((BASE_DIR.parent.parent).glob("*.json"))
			candidates += list(secrets_dir.glob("*.json")) if secrets_dir.exists() else []
			gp_secrets = (BASE_DIR.parent.parent / "secrets")
			candidates += list(gp_secrets.glob("*.json")) if gp_secrets.exists() else []
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
		except Exception as exc:
			raise RuntimeError("Provide GOOGLE_SERVICE_ACCOUNT_INFO or GOOGLE_SERVICE_ACCOUNT_FILE") from exc
	return build("drive", "v3", credentials=creds, cache_discovery=False)


@app.post("/save_drive")
async def save_drive(payload: Dict[str, Any]):
	name = payload.get("name") or _active_db_name
	folder_id = payload.get("folder_id") or os.getenv("DRIVE_FOLDER_ID")
	try:
		db = _db_registry[name]
		content = json.dumps(db.to_json(), ensure_ascii=False).encode("utf-8")
		drive = _get_drive_service(["https://www.googleapis.com/auth/drive.file"])
		body: Dict[str, Any] = {"name": f"{name}.json"}
		if folder_id:
			body["parents"] = [folder_id]
		else:
			# Service accounts have no personal storage; require a shared drive folder
			raise HTTPException(status_code=400, detail="Provide a shared drive folder_id (or set DRIVE_FOLDER_ID env)")
		media = MediaInMemoryUpload(body=content, mimetype="application/json", resumable=False)  # type: ignore[arg-type]
		file = drive.files().create(body=body, media_body=media, fields="id", supportsAllDrives=True).execute()
		return {"status": "ok", "file_id": file.get("id")}
	except HTTPException:
		raise
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


@app.get("/drive_files")
async def list_drive_files():
	try:
		drive = _get_drive_service(["https://www.googleapis.com/auth/drive.readonly"])
		files = []
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


