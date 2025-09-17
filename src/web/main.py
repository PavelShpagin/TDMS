from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.database import Database

import json
import os
import io
import re

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

# Multi-database registry
_db_registry: Dict[str, Database] = {}
_active_db_name: str = "default"
_db_registry[_active_db_name] = Database(name=_active_db_name)


def get_db() -> Database:
	return _db_registry[_active_db_name]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
	# Detect Google OAuth client id (env first, then secrets/client_secret_*.json)
	client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
	if not client_id:
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
				if "web" in data and "client_id" in data["web"]:
					client_id = data["web"]["client_id"]
					break
		except Exception:
			client_id = None
	context = {
		"request": request,
		"tables": [t.to_json() for t in get_db().tables.values()],
		"google_client_id": client_id or "",
		"google_api_key": os.getenv("GOOGLE_API_KEY", ""),
		"google_app_id": os.getenv("GOOGLE_PICKER_APP_ID", ""),
	}
	return templates.TemplateResponse("index.html", context)


# Database management
@app.get("/databases")
def list_databases():
	return {"active": _active_db_name, "databases": sorted(_db_registry.keys())}


@app.post("/create_database")
async def create_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	if not name:
		raise HTTPException(status_code=400, detail="Provide database name")
	if name in _db_registry:
		raise HTTPException(status_code=400, detail="Database already exists")
	_db_registry[name] = Database(name=name)
	_active_db_name = name
	return {"status": "ok", "active": _active_db_name}


@app.post("/switch_database")
async def switch_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	if not name or name not in _db_registry:
		raise HTTPException(status_code=400, detail="Unknown database")
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
	_db_registry.pop(name, None)
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


@app.post("/import_database")
async def import_database(payload: Dict[str, Any]):
	global _active_db_name
	name = payload.get("name")
	data = payload.get("data")
	if not name or not isinstance(data, dict):
		raise HTTPException(status_code=400, detail="Provide name and data")
	try:
		db = Database.from_json(data)
		db.name = name
		_db_registry[name] = db
		_active_db_name = name
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


