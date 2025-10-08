import json
import os
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.oauth2 import service_account
import redis


class DriveService:
    """
    Google Drive service using the same service-account configuration
    as web save/load endpoints. No user OAuth; suitable for Celery workers.
    """

    def __init__(self, access_token: Optional[str] = None, scopes: Optional[list[str]] = None):
        scopes = scopes or ["https://www.googleapis.com/auth/drive.file"]

        creds = None

        # Priority 1: Use provided access token (from Redis or caller)
        if access_token:
            from google.oauth2.credentials import Credentials  # lazy import

            creds = Credentials(token=access_token)
            # Note: discovery build will use bearer token directly; no refresh
            self.service = build("drive", "v3", credentials=creds)
            return

        # Priority 2: GOOGLE_SERVICE_ACCOUNT_INFO (JSON) or GOOGLE_SERVICE_ACCOUNT_FILE (path)
        info_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_INFO")
        file_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if info_env:
            try:
                creds = service_account.Credentials.from_service_account_info(
                    json.loads(info_env), scopes=scopes  # type: ignore[arg-type]
                )
            except Exception as exc:
                raise RuntimeError("Invalid GOOGLE_SERVICE_ACCOUNT_INFO") from exc
        elif file_env:
            p = Path(file_env)
            if not p.exists():
                # Try common locations
                candidates = [
                    Path.cwd() / file_env,
                    Path.cwd() / "secrets" / file_env,
                    Path(__file__).resolve().parents[2] / file_env,
                    Path(__file__).resolve().parents[2] / "secrets" / file_env,
                ]
                for c in candidates:
                    if c.exists():
                        p = c
                        break
            creds = service_account.Credentials.from_service_account_file(
                str(p), scopes=scopes  # type: ignore[arg-type]
            )
        else:
            # Fallback: auto-detect a service account JSON in project root and /secrets
            root = Path.cwd()
            secrets_dir = root / "secrets"
            candidates: list[Path] = []
            candidates += list(root.glob("*.json"))
            candidates += list(Path(__file__).resolve().parents[2].glob("*.json"))
            if secrets_dir.exists():
                candidates += list(secrets_dir.glob("*.json"))
            gp_secrets = Path(__file__).resolve().parents[2] / "secrets"
            if gp_secrets.exists():
                candidates += list(gp_secrets.glob("*.json"))

            for candidate in candidates:
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    if (
                        data.get("type") == "service_account"
                        and "client_email" in data
                        and "private_key" in data
                    ):
                        creds = service_account.Credentials.from_service_account_file(
                            str(candidate), scopes=scopes  # type: ignore[arg-type]
                        )
                        break
                except Exception:
                    continue

            if creds is None:
                raise RuntimeError(
                    "Provide GOOGLE_SERVICE_ACCOUNT_INFO or GOOGLE_SERVICE_ACCOUNT_FILE or place a service account JSON in ./ or ./secrets"
                )

        self.service = build("drive", "v3", credentials=creds)

    def upload_or_update(self, db_name: str, db_data: dict) -> str:
        filename = f"{db_name}.json"
        content = json.dumps(db_data, ensure_ascii=False, indent=2)
        media = MediaInMemoryUpload(
            content.encode("utf-8"), mimetype="application/json", resumable=True
        )

        # If a target folder is specified, constrain search and upload
        folder_id = os.getenv("DRIVE_FOLDER_ID")
        if folder_id:
            query = (
                f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            )
        else:
            query = f"name='{filename}' and trashed=false"

        results = (
            self.service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files = results.get("files", [])

        if files:
            file_id = files[0]["id"]
            self.service.files().update(
                fileId=file_id, media_body=media, supportsAllDrives=True
            ).execute()
            return file_id

        file_metadata: dict[str, object] = {
            "name": filename,
            "mimeType": "application/json",
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]

        file = (
            self.service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
        return file.get("id")

    def delete_by_name(self, db_name: str) -> bool:
        """Delete a database file from Drive by name. Returns True if deleted.
        Respects DRIVE_FOLDER_ID and Shared Drives.
        """
        filename = f"{db_name}.json"
        folder_id = os.getenv("DRIVE_FOLDER_ID")
        if folder_id:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        else:
            query = f"name='{filename}' and trashed=false"

        results = (
            self.service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            return False
        file_id = files[0]["id"]
        self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        return True


