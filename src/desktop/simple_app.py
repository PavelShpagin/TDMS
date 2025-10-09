"""
Desktop TDMS application that uses the exact same web interface as the web version.
This ensures 100% consistency between web and desktop versions.
"""

import threading
import time
import atexit
from pathlib import Path

import webview
import webbrowser
import uvicorn

# Load environment variables before importing the web app
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
    print("Loaded .env file for desktop app")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

# Import the web application
from src.web.main import app

# Start OAuth callback server
try:
    from src.desktop.oauth_server import get_oauth_server
    oauth_server = get_oauth_server()
    print("OAuth callback server started on http://localhost:8080")
except Exception as e:
    print(f"Warning: Could not start OAuth callback server: {e}")
    oauth_server = None


class DesktopAPI:
    """Enhanced desktop API with file operations"""
    
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
            
            from src.core.database import Database
            
            file_paths = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=str(Path.home()),
                file_types=("JSON files (*.json)",)
            )
            
            if not file_paths or len(file_paths) == 0:
                return {"status": "cancelled"}
            
            file_path = file_paths[0]
            
            try:
                db = Database.load(file_path)
                
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
            
            import csv
            
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            if table_name not in db.tables:
                return {"status": "error", "message": f"Table '{table_name}' not found"}
            
            table = db.tables[table_name]
            
            file_path = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=str(Path.home()),
                save_filename=f"{table_name}.csv",
                file_types=("CSV files (*.csv)",)
            )
            
            if not file_path:
                return {"status": "cancelled"}
            
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
            
            return {"status": "ok", "path": file_path, "rows": len(table.rows)}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def import_csv_table(self) -> dict:
        """Import a CSV file as a new table"""
        try:
            if not self.window:
                return {"status": "error", "message": "Window not initialized"}
            
            import csv
            from src.core.column import Column
            
            file_paths = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=str(Path.home()),
                file_types=("CSV files (*.csv)",)
            )
            
            if not file_paths or len(file_paths) == 0:
                return {"status": "cancelled"}
            
            file_path = file_paths[0]
            table_name = Path(file_path).stem
            
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                if len(rows) == 0:
                    return {"status": "error", "message": "CSV file is empty"}
                
                fieldnames = reader.fieldnames
                if not fieldnames:
                    return {"status": "error", "message": "CSV file has no columns"}
                
                columns = []
                for field in fieldnames:
                    col_type = "string"
                    sample_values = [row[field] for row in rows[:min(10, len(rows))] if row.get(field)]
                    
                    if sample_values:
                        try:
                            all_ints = all(str(v).isdigit() or (str(v).startswith('-') and str(v)[1:].isdigit()) 
                                         for v in sample_values if v)
                            if all_ints:
                                col_type = "integer"
                        except:
                            pass
                        
                        if col_type == "string":
                            try:
                                all_floats = all(float(str(v).replace(',', '')) or True 
                                               for v in sample_values if v)
                                if all_floats:
                                    col_type = "real"
                            except:
                                pass
                    
                    columns.append(Column(name=field, type_name=col_type))
                
                table = db.create_table(table_name, [col.to_json() for col in columns])
                
                for row in rows:
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
            from src.core.database import Database
            
            state = getattr(app.state, "app_state", None)
            if not state:
                return {"status": "error", "message": "App state not initialized"}
            
            base_name = "new_database"
            db_name = base_name
            counter = 1
            while db_name in state.db_registry:
                db_name = f"{base_name}_{counter}"
                counter += 1
            
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
            
            import csv
            
            state = getattr(app.state, "app_state", None)
            if not state or not state.db_registry.get(state.active_db_name):
                return {"status": "error", "message": "No active database"}
            
            db = state.db_registry[state.active_db_name]
            
            if len(db.tables) == 0:
                return {"status": "error", "message": "No tables to export"}
            
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


class DesktopServer:
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.port = self._find_free_port()
        
        self.storage_dir = Path("desktop_databases")
        self.storage_dir.mkdir(exist_ok=True)
        
        atexit.register(self._cleanup)

    def _find_free_port(self):
        """Find a free port for desktop app, avoid 8000 (reserved for web)"""
        import socket
        for port in range(8001, 8100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return 8001

    def _cleanup(self):
        """Cleanup on exit"""
        if self.server:
            print("Shutting down desktop server...")

    def start_server(self):
        """Start the FastAPI server in a separate thread"""
        try:
            uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="warning")
        except Exception as e:
            print(f"Server error: {e}")

    def run(self):
        """Run the desktop application"""
        print(f"Starting TDMS Desktop on port {self.port}")
        
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        time.sleep(3)
        
        api = DesktopAPI()
        
        window = webview.create_window(
            "TDMS Desktop Application",
            f"http://127.0.0.1:{self.port}?desktop=true",
            width=1400,
            height=900,
            min_size=(1000, 700),
            resizable=True,
            js_api=api,
        )
        
        api.set_window(window)
        
        webview.start(debug=False, gui='edgechromium')


def main() -> None:
    """Main function to start the desktop application"""
    desktop_app = DesktopServer()
    desktop_app.run()


if __name__ == "__main__":
    main()
