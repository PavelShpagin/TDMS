from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from .app_factory import create_app
from .config import get_settings

app = create_app()

# In-memory OAuth state store for desktop loopback flow
_oauth_states: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    import json

    settings = get_settings()
    user_agent = request.headers.get("user-agent", "").lower()
    port = request.url.port
    # Detect desktop by query flag, user agent, or non-default port
    desktop_flag = (request.query_params.get("desktop") or "").lower() in ("1", "true", "yes")
    is_desktop = desktop_flag or ("pywebview" in user_agent) or (port != 8000 and port is not None)

    client_id = settings.google_oauth_client_id
    client_secret = settings.google_oauth_client_secret

    if not client_id:
        try:
            base_dir = Path(__file__).resolve().parent
            root = Path.cwd()
            secrets_dir = root / "secrets"
            candidates: List[Path] = []
            candidates += list(root.glob("client_secret*.json"))
            candidates += list((base_dir.parent.parent).glob("client_secret*.json"))
            if secrets_dir.exists():
                candidates += list(secrets_dir.glob("client_secret*.json"))
            gp_secrets = base_dir.parent.parent / "secrets"
            if gp_secrets.exists():
                candidates += list(gp_secrets.glob("client_secret*.json"))

            for f in candidates:
                data = json.loads(f.read_text(encoding="utf-8"))
                key = "installed" if is_desktop else "web"
                if key in data and "client_id" in data[key]:
                    client_id = data[key]["client_id"]
                    client_secret = data[key]["client_secret"]
                    break

            if not client_id:
                for f in candidates:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    for key in ("web", "installed"):
                        if key in data and "client_id" in data[key]:
                            client_id = data[key]["client_id"]
                            client_secret = data[key]["client_secret"]
                            break
                    if client_id:
                        break
        except Exception:
            client_id = None
            client_secret = None

    # Collect table list from app state (if available)
    tables: List[Dict[str, Any]] = []
    try:
        state = getattr(app.state, "app_state", None)
        if state and state.db_registry.get(state.active_db_name):
            tables = [t.to_json() for t in state.db_registry[state.active_db_name].tables.values()]
    except Exception:
        pass

    context = {
        "request": request,
        "tables": tables,
        "google_client_id": client_id or "",
        # Only expose client secret to desktop app context
        "google_client_secret": (client_secret or "") if is_desktop else "",
        "google_api_key": (settings.google_api_key or "") if not is_desktop else "",
        "google_app_id": (settings.google_picker_app_id or "") if not is_desktop else "",
        "google_refresh_token": (settings.google_refresh_token or "") if is_desktop else "",
        "is_desktop": is_desktop,
    }
    return app.state.templates.TemplateResponse("index.html", context)


@app.get("/oauth/callback")
def oauth_callback(request: Request):
    """Desktop loopback redirect target. Stores code by state and shows a tiny page."""
    try:
        params = dict(request.query_params)
        state = params.get("state")
        code = params.get("code")
        error = params.get("error")
        if state:
            _oauth_states[state] = {"code": code, "error": error}
        html = """
<!doctype html>
<html><head><meta charset="utf-8"><title>Authentication complete</title></head>
<body style="font-family:system-ui,Segoe UI,Arial,sans-serif;">
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
    
    # Check in-memory store first (for web loopback)
    data = _oauth_states.get(state)
    if data:
        return JSONResponse({"status": "ok", **data})
    
    # Check OAuth callback server (for desktop)
    try:
        from src.desktop.oauth_server import OAuthCallbackHandler
        if state in OAuthCallbackHandler.received_codes:
            data = OAuthCallbackHandler.received_codes[state]
            return JSONResponse({"status": "ok", **data})
    except ImportError:
        pass  # OAuth server not available
    
    return JSONResponse({"status": "pending"})
