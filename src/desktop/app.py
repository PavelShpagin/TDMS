from __future__ import annotations

import json
import threading
import time
import webbrowser
from pathlib import Path

import webview
import uvicorn

from src.web.main import app
from src.core.database import Database
from src.core.operations import union_tables


def start_server():
    """Start the FastAPI server in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main() -> None:
    """Main function to start the desktop application"""
    # Start the FastAPI server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    # Create the webview window pointing to the local server
    window = webview.create_window(
        "TDMS Desktop Application",
        "http://127.0.0.1:8000",
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True
    )
    
    # Start the webview
    webview.start(debug=False)


def build_desktop() -> None:
    """Build the desktop application (for future packaging)"""
    print("Building desktop application...")
    print("Desktop app is ready to run with: python -m src.desktop.app")
    print("For creating an executable, you can use PyInstaller:")
    print("pip install pyinstaller")
    print("pyinstaller --onefile --windowed --name TDMS-Desktop src/desktop/app.py")


# Desktop API class for testing
class API:
    def __init__(self) -> None:
        self.db = Database(name="desktop")

    def create_table(self, name: str, schema_json: str) -> dict:
        schema = json.loads(schema_json)
        table = self.db.create_table(name, schema)
        return table.to_json()

    def insert_row(self, table: str, values_json: str) -> dict:
        values = json.loads(values_json)
        self.db.insert_row(table, values)
        return {"status": "ok"}

    def union(self, left: str, right: str) -> dict:
        t1 = self.db.get_table(left)
        t2 = self.db.get_table(right)
        
        union_table = union_tables(t1, t2)
        
        # Handle duplicate names
        base_name = union_table.name
        union_name = base_name
        counter = 2
        while union_name in self.db.tables:
            union_name = f"{base_name}_{counter}"
            counter += 1
        
        union_table.name = union_name
        self.db.tables[union_name] = union_table
        return union_table.to_json()

    def save(self, path: str = "") -> dict:
        if not path:
            path = str(Path.cwd() / "database.json")
        self.db.save(path)
        return {"path": path}

    def load(self, path: str) -> dict:
        self.db = Database.load(path)
        return {"status": "ok"}

    def dump(self) -> dict:
        return self.db.to_json()

    def delete_table(self, name: str) -> dict:
        if name not in self.db.tables:
            raise ValueError(f"Table '{name}' does not exist")
        del self.db.tables[name]
        return {"status": "deleted", "name": name}


if __name__ == "__main__":
    main()


