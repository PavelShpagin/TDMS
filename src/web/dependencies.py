from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator, Dict

from fastapi import Depends, Request

from src.core.database import Database
from .config import Settings, get_settings


class AppState:
    """Application runtime state shared via DI.

    Holds database registry and active database name.
    """

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.db_registry: Dict[str, Database] = {}
        self.active_db_name: str = "default"

    def get_db_file_path(self, db_name: str) -> Path:
        return self.storage_dir / f"{db_name}.json"

    def load_or_create_database(self, db_name: str) -> Database:
        db_file = self.get_db_file_path(db_name)
        if db_file.exists():
            try:
                return Database.load(str(db_file))
            except Exception:
                # Create new on failure to ensure availability
                return Database(name=db_name)
        return Database(name=db_name)

    def save_database(self, db_name: str) -> None:
        if db_name in self.db_registry:
            db_file = self.get_db_file_path(db_name)
            self.db_registry[db_name].save(str(db_file))


async def get_app_state(request: Request) -> AppState:
    """Get the app-wide shared AppState from app.state.
    
    This ensures all requests share the same state, preventing
    issues where databases created in one request aren't visible in another.
    """
    return request.app.state.app_state


def get_active_db(state: AppState = Depends(get_app_state)) -> Database:
    return state.db_registry[state.active_db_name]


