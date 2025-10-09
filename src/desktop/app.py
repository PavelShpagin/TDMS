from __future__ import annotations

import json
import csv
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import webview
import uvicorn

from src.web.main import app
from src.core.database import Database
from src.core.operations import union_tables
from src.core.column import Column


def start_server():
    """Start the FastAPI server in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


class DesktopAPI:
    """API for desktop-specific operations"""
    
    def __init__(self):
        self.window = None
    
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
    
    def open_url(self, url: str) -> dict:
        """Open URL in system default browser"""
        try:
            webbrowser.open(url)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def save_database_file(self) -> dict:
        """Save current database to a file selected by user"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(Path.home()),
                save_filename="database.json",
                file_types=("JSON files (*.json)",)
            )
            
            if not file_path:
                return {"status": "cancelled"}
            
            # Get the current database from app state
            try:
                state = getattr(app.state, "app_state", None)
                if not state or not state.db_registry.get(state.active_db_name):
                    return {"status": "error", "message": "No active database"}
                
                db = state.db_registry[state.active_db_name]
                db.save(file_path)
                return {"status": "ok", "path": file_path}
            except Exception as e:
                return {"status": "error", "message": f"Failed to save: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def load_database_file(self) -> dict:
        """Load database from a file selected by user"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            file_paths = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=str(Path.home()),
                file_types=("JSON files (*.json)",)
            )
            
            if not file_paths or len(file_paths) == 0:
                return {"status": "cancelled"}
            
            file_path = file_paths[0]
            
            # Load the database
            try:
                db = Database.load(file_path)
                
                # Register it in app state
                state = getattr(app.state, "app_state", None)
                if state:
                    # Get base name and handle duplicates
                    base_name = Path(file_path).stem
                    db_name = base_name
                    counter = 1
                    
                    # If database name already exists, add (1), (2), etc.
                    while db_name in state.db_registry:
                        db_name = f"{base_name} ({counter})"
                        counter += 1
                    
                    state.db_registry[db_name] = db
                    state.active_db_name = db_name
                
                return {"status": "ok", "path": file_path, "database": db.to_json(), "name": db_name}
            except Exception as e:
                return {"status": "error", "message": f"Failed to load: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def export_table_csv(self, table_name: str) -> dict:
        """Export a table to CSV file"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            # Get the table
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            if table_name not in db.tables:
                return {"status": "error", "message": f"Table '{table_name}' not found"}
            
            table = db.tables[table_name]
            
            # Select file to save
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(Path.home()),
                save_filename=f"{table_name}.csv",
                file_types=("CSV files (*.csv)",)
            )
            
            if not file_path:
                return {"status": "cancelled"}
            
            # Export to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                if len(table.rows) == 0:
                    # Write only headers
                    writer = csv.writer(csvfile)
                    writer.writerow([col.name for col in table.columns])
                else:
                    # Write headers and data
                    fieldnames = [col.name for col in table.columns]
                    dict_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    dict_writer.writeheader()
                    for row in table.rows:
                        dict_writer.writerow({col.name: row.values.get(col.name) for col in table.columns})
            
            return {"status": "ok", "path": file_path, "rows": len(table.rows)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def import_csv_table(self) -> dict:
        """Import a CSV file as a new table"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            # Select file to import
            file_paths = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=str(Path.home()),
                file_types=("CSV files (*.csv)",)
            )
            
            if not file_paths or len(file_paths) == 0:
                return {"status": "cancelled"}
            
            file_path = file_paths[0]
            table_name = Path(file_path).stem
            
            # Get the database
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            
            # Read CSV and infer schema
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                if len(rows) == 0:
                    return {"status": "error", "message": "CSV file is empty"}
                
                # Infer column types from first few rows
                fieldnames = reader.fieldnames
                if not fieldnames:
                    return {"status": "error", "message": "CSV file has no columns"}
                
                columns = []
                for field in fieldnames:
                    # Try to infer type from values
                    col_type = "string"  # default
                    sample_values = [row[field] for row in rows[:min(10, len(rows))] if row.get(field)]
                    
                    if sample_values:
                        # Check if all values are integers
                        try:
                            all_ints = all(str(v).isdigit() or (str(v).startswith('-') and str(v)[1:].isdigit()) 
                                         for v in sample_values if v)
                            if all_ints:
                                col_type = "integer"
                        except:
                            pass
                        
                        # Check if all values are floats
                        if col_type == "string":
                            try:
                                all_floats = all(float(str(v).replace(',', '')) or True 
                                               for v in sample_values if v)
                                if all_floats:
                                    col_type = "real"
                            except:
                                pass
                    
                    columns.append(Column(name=field, type_name=col_type))
                
                # Create table
                table = db.create_table(table_name, [col.to_json() for col in columns])
                
                # Insert rows
                for row in rows:
                    # Convert values to appropriate types
                    values: dict = {}
                    for col in columns:
                        value = row.get(col.name, "")
                        if value == "":
                            values[col.name] = None
                        elif col.type_name == "integer":
                            try:
                                values[col.name] = int(value)
                            except:
                                values[col.name] = None
                        elif col.type_name == "real":
                            try:
                                values[col.name] = float(value.replace(',', ''))
                            except:
                                values[col.name] = None
                        else:
                            values[col.name] = str(value)
                    
                    db.insert_row(table_name, values)
                
                return {
                    "status": "ok",
                    "path": file_path,
                    "table": table.to_json(),
                    "rows_imported": len(rows)
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def new_database(self) -> dict:
        """Create a new empty database"""
        try:
            state = getattr(app.state, "app_state", None)
            if not state:
                return {"status": "error", "message": "App state not initialized"}
            
            # Generate a new database name
            base_name = "new_database"
            db_name = base_name
            counter = 1
            while db_name in state.db_registry:
                db_name = f"{base_name}_{counter}"
                counter += 1
            
            # Create new database
            db = Database(name=db_name)
            state.db_registry[db_name] = db
            state.active_db_name = db_name
            
            return {"status": "ok", "database": db_name}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def download_database(self, db_name: str) -> dict:
        """Download a specific database as JSON file"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            state = getattr(app.state, "app_state", None)
            if not state or db_name not in state.db_registry:
                return {"status": "error", "message": f"Database '{db_name}' not found"}
            
            db = state.db_registry[db_name]
            
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(Path.home()),
                save_filename=f"{db_name}.json",
                file_types=("JSON files (*.json)",)
            )
            
            if not file_path:
                return {"status": "cancelled"}
            
            db.save(file_path)
            return {"status": "ok", "path": file_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def download_all_databases(self) -> dict:
        """Download all databases as JSON files to a selected directory"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            state = getattr(app.state, "app_state", None)
            if not state:
                return {"status": "error", "message": "App state not initialized"}
            
            if not state.db_registry:
                return {"status": "error", "message": "No databases available"}
            
            # Count non-default databases
            databases_to_save = {name: db for name, db in state.db_registry.items() if name != "default"}
            
            if not databases_to_save:
                return {"status": "error", "message": "No databases to download (only default exists)"}
            
            # Select directory - note: FOLDER_DIALOG returns a tuple with single path
            try:
                directory = self.window.create_file_dialog(
                    webview.FOLDER_DIALOG,
                    directory=str(Path.home())
                )
            except Exception as dialog_error:
                return {"status": "error", "message": f"Dialog error: {str(dialog_error)}"}
            
            # Handle dialog cancellation or empty result
            if not directory:
                return {"status": "cancelled"}
            
            # Get the directory path from the result
            # create_file_dialog with FOLDER_DIALOG returns tuple or list with one element
            if isinstance(directory, (list, tuple)):
                if len(directory) == 0:
                    return {"status": "cancelled"}
                dir_path = str(directory[0])
            else:
                dir_path = str(directory)
            
            # Validate directory path
            dir_path_obj = Path(dir_path)
            if not dir_path_obj.exists():
                return {"status": "error", "message": f"Selected directory does not exist: {dir_path}"}
            
            if not dir_path_obj.is_dir():
                return {"status": "error", "message": f"Selected path is not a directory: {dir_path}"}
            
            downloaded = 0
            errors = []
            
            for db_name, db in databases_to_save.items():
                try:
                    # Sanitize filename to avoid invalid characters
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in db_name)
                    
                    # Handle duplicate filenames by adding (1), (2), etc.
                    base_file_path = dir_path_obj / f"{safe_name}.json"
                    file_path = base_file_path
                    counter = 1
                    
                    while file_path.exists():
                        # Remove .json extension, add (counter), then add .json back
                        file_path = dir_path_obj / f"{safe_name} ({counter}).json"
                        counter += 1
                    
                    db.save(str(file_path))
                    downloaded += 1
                except Exception as e:
                    errors.append(f"{db_name}: {str(e)}")
            
            if errors:
                error_msg = "; ".join(errors)
                return {"status": "partial", "directory": dir_path, "databases_downloaded": downloaded, 
                       "errors": error_msg, "message": f"Downloaded {downloaded}, but had errors: {error_msg}"}
            
            return {"status": "ok", "directory": dir_path, "databases_downloaded": downloaded}
        except Exception as e:
            import traceback
            return {"status": "error", "message": f"{str(e)}", "trace": traceback.format_exc()}
    
    def export_all_tables_csv(self) -> dict:
        """Export all tables from active database to CSV files"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            
            if len(db.tables) == 0:
                return {"status": "error", "message": "No tables to export"}
            
            # Select directory
            try:
                directory = self.window.create_file_dialog(
                    webview.FOLDER_DIALOG,
                    directory=str(Path.home())
                )
            except Exception as dialog_error:
                return {"status": "error", "message": f"Dialog error: {str(dialog_error)}"}
            
            if not directory:
                return {"status": "cancelled"}
            
            # Get the directory path from the result
            if isinstance(directory, (list, tuple)):
                if len(directory) == 0:
                    return {"status": "cancelled"}
                dir_path = str(directory[0])
            else:
                dir_path = str(directory)
            
            # Validate directory path
            dir_path_obj = Path(dir_path)
            if not dir_path_obj.exists() or not dir_path_obj.is_dir():
                return {"status": "error", "message": f"Invalid directory: {dir_path}"}
            
            exported = 0
            
            for table_name, table in db.tables.items():
                file_path = dir_path_obj / f"{table_name}.csv"
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    if len(table.rows) == 0:
                        writer = csv.writer(csvfile)
                        writer.writerow([col.name for col in table.columns])
                    else:
                        fieldnames = [col.name for col in table.columns]
                        dict_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        dict_writer.writeheader()
                        for row in table.rows:
                            dict_writer.writerow({col.name: row.values.get(col.name) for col in table.columns})
                
                exported += 1
            
            return {"status": "ok", "directory": dir_path, "tables_exported": exported}
        except Exception as e:
            import traceback
            return {"status": "error", "message": f"{str(e)}", "trace": traceback.format_exc()}


def main() -> None:
    """Main function to start the desktop application"""
    # Start the FastAPI server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    # Create API instance for JavaScript bridge
    api = DesktopAPI()
    
    # Create the webview window pointing to the local server
    window = webview.create_window(
        "TDMS Desktop Application",
        "http://127.0.0.1:8000?desktop=true",
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        js_api=api  # Expose API to JavaScript
    )
    
    # Set window reference in API after window creation
    api.set_window(window)
    
    # Start the webview with better settings
    webview.start(debug=False, gui='edgechromium')  # Use EdgeChromium for better compatibility


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
            union_name = f"{base_name} ({counter})"
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


