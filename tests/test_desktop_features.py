from __future__ import annotations

import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

from src.desktop.app import DesktopAPI
from src.core.database import Database
from src.core.table import Table
from src.core.column import Column


class TestDesktopAPI:
    """Test the enhanced DesktopAPI with file operations"""

    @pytest.fixture
    def api(self):
        """Create a DesktopAPI instance"""
        api = DesktopAPI()
        mock_window = MagicMock()
        api.set_window(mock_window)
        return api

    @pytest.fixture
    def mock_app_state(self):
        """Create a mock app state with a test database"""
        db = Database(name="test_db")
        schema = [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "value", "type": "real"}
        ]
        table = db.create_table("test_table", schema)
        db.insert_row("test_table", {"id": 1, "name": "Alice", "value": 10.5})
        db.insert_row("test_table", {"id": 2, "name": "Bob", "value": 20.3})
        
        mock_state = MagicMock()
        mock_state.db_registry = {"test_db": db}
        mock_state.active_db_name = "test_db"
        
        return mock_state

    def test_api_initialization(self):
        """Test DesktopAPI initialization"""
        api = DesktopAPI()
        assert api.window is None
        
        mock_window = MagicMock()
        api.set_window(mock_window)
        assert api.window is mock_window

    def test_open_url(self, api):
        """Test opening URL in browser"""
        with patch('webbrowser.open') as mock_open:
            result = api.open_url("https://example.com")
            assert result["status"] == "ok"
            mock_open.assert_called_once_with("https://example.com")

    def test_open_url_error(self, api):
        """Test open URL error handling"""
        with patch('webbrowser.open', side_effect=Exception("Browser error")):
            result = api.open_url("https://example.com")
            assert result["status"] == "error"
            assert "Browser error" in result["message"]

    def test_save_database_file_success(self, api, mock_app_state, tmp_path):
        """Test saving database to file"""
        save_path = str(tmp_path / "test_save.json")
        api.window.create_file_dialog.return_value = save_path
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.save_database_file()
            
            assert result["status"] == "ok"
            assert result["path"] == save_path
            api.window.create_file_dialog.assert_called_once()
            
            assert Path(save_path).exists()

    def test_save_database_file_cancelled(self, api):
        """Test cancelling save database dialog"""
        api.window.create_file_dialog.return_value = None
        
        result = api.save_database_file()
        assert result["status"] == "cancelled"

    def test_save_database_no_active_db(self, api):
        """Test saving when no active database"""
        api.window.create_file_dialog.return_value = "/path/to/file.json"
        
        mock_state = MagicMock()
        mock_state.db_registry = {}
        mock_state.active_db_name = "nonexistent"
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            result = api.save_database_file()
            assert result["status"] == "error"
            assert "No active database" in result["message"]

    def test_load_database_file_success(self, api, tmp_path):
        """Test loading database from file"""
        db = Database(name="loaded_db")
        schema = [{"name": "id", "type": "integer"}, {"name": "data", "type": "string"}]
        db.create_table("loaded_table", schema)
        
        load_path = tmp_path / "test_load.json"
        db.save(str(load_path))
        
        api.window.create_file_dialog.return_value = [str(load_path)]
        
        mock_state = MagicMock()
        mock_state.db_registry = {}
        mock_state.active_db_name = None
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            result = api.load_database_file()
            
            assert result["status"] == "ok"
            assert result["path"] == str(load_path)
            assert "database" in result
            api.window.create_file_dialog.assert_called_once()

    def test_load_database_file_cancelled(self, api):
        """Test cancelling load database dialog"""
        api.window.create_file_dialog.return_value = []
        
        result = api.load_database_file()
        assert result["status"] == "cancelled"

    def test_load_database_file_error(self, api, tmp_path):
        """Test loading invalid database file"""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("invalid json")
        
        api.window.create_file_dialog.return_value = [str(bad_file)]
        
        mock_state = MagicMock()
        mock_state.db_registry = {}
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            result = api.load_database_file()
            assert result["status"] == "error"
            assert "Failed to load" in result["message"]

    def test_export_table_csv_success(self, api, mock_app_state, tmp_path):
        """Test exporting table to CSV"""
        csv_path = str(tmp_path / "test_export.csv")
        api.window.create_file_dialog.return_value = csv_path
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.export_table_csv("test_table")
            
            assert result["status"] == "ok"
            assert result["path"] == csv_path
            assert result["rows"] == 2
            api.window.create_file_dialog.assert_called_once()
            
            assert Path(csv_path).exists()
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["name"] == "Alice"
                assert rows[1]["name"] == "Bob"

    def test_export_table_csv_cancelled(self, api, mock_app_state):
        """Test cancelling CSV export"""
        api.window.create_file_dialog.return_value = None
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.export_table_csv("test_table")
            assert result["status"] == "cancelled"

    def test_export_table_csv_nonexistent_table(self, api, mock_app_state):
        """Test exporting nonexistent table"""
        api.window.create_file_dialog.return_value = "/path/to/file.csv"
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.export_table_csv("nonexistent_table")
            assert result["status"] == "error"
            assert "not found" in result["message"]

    def test_export_empty_table_csv(self, api, mock_app_state, tmp_path):
        """Test exporting empty table to CSV"""
        db = mock_app_state.db_registry["test_db"]
        schema = [{"name": "col1", "type": "string"}, {"name": "col2", "type": "integer"}]
        db.create_table("empty_table", schema)
        
        csv_path = str(tmp_path / "empty.csv")
        api.window.create_file_dialog.return_value = csv_path
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.export_table_csv("empty_table")
            
            assert result["status"] == "ok"
            assert result["rows"] == 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "col1" in content
                assert "col2" in content

    def test_import_csv_table_success(self, api, mock_app_state, tmp_path):
        """Test importing CSV as table"""
        csv_path = tmp_path / "import.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "score"])
            writer.writeheader()
            writer.writerow({"id": "1", "name": "Alice", "score": "95.5"})
            writer.writerow({"id": "2", "name": "Bob", "score": "88.3"})
            writer.writerow({"id": "3", "name": "Charlie", "score": "92.1"})
        
        api.window.create_file_dialog.return_value = [str(csv_path)]
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.import_csv_table()
            
            assert result["status"] == "ok"
            assert result["path"] == str(csv_path)
            assert result["rows_imported"] == 3
            assert "table" in result
            api.window.create_file_dialog.assert_called_once()
            
            db = mock_app_state.db_registry["test_db"]
            assert "import" in db.tables
            imported_table = db.tables["import"]
            assert len(imported_table.rows) == 3

    def test_import_csv_table_cancelled(self, api):
        """Test cancelling CSV import"""
        api.window.create_file_dialog.return_value = []
        
        result = api.import_csv_table()
        assert result["status"] == "cancelled"

    def test_import_csv_table_empty_file(self, api, mock_app_state, tmp_path):
        """Test importing empty CSV file"""
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["col1", "col2"])
            writer.writeheader()
        
        api.window.create_file_dialog.return_value = [str(csv_path)]
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.import_csv_table()
            assert result["status"] == "error"
            assert "empty" in result["message"].lower()

    def test_import_csv_type_inference(self, api, mock_app_state, tmp_path):
        """Test CSV import correctly infers column types"""
        csv_path = tmp_path / "types.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["int_col", "float_col", "str_col"])
            writer.writeheader()
            writer.writerow({"int_col": "42", "float_col": "3.14", "str_col": "hello"})
            writer.writerow({"int_col": "100", "float_col": "2.71", "str_col": "world"})
        
        api.window.create_file_dialog.return_value = [str(csv_path)]
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_app_state
            
            result = api.import_csv_table()
            
            assert result["status"] == "ok"
            
            db = mock_app_state.db_registry["test_db"]
            table = db.tables["types"]
            
            col_types = {col.name: col.type_name for col in table.columns}
            assert col_types["int_col"] == "integer"
            assert col_types["float_col"] == "real"
            assert col_types["str_col"] == "string"

    def test_new_database(self, api):
        """Test creating new database"""
        mock_state = MagicMock()
        mock_state.db_registry = {}
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            result = api.new_database()
            
            assert result["status"] == "ok"
            assert "database" in result
            assert result["database"] == "new_database"
            assert "new_database" in mock_state.db_registry
            assert mock_state.active_db_name == "new_database"

    def test_new_database_multiple(self, api):
        """Test creating multiple new databases"""
        mock_state = MagicMock()
        mock_state.db_registry = {}
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            result1 = api.new_database()
            assert result1["database"] == "new_database"
            
            result2 = api.new_database()
            assert result2["database"] == "new_database_1"
            
            result3 = api.new_database()
            assert result3["database"] == "new_database_2"

    def test_api_without_window(self):
        """Test API methods fail gracefully without window"""
        api = DesktopAPI()
        
        result = api.save_database_file()
        assert result["status"] == "error"
        assert "Window not initialized" in result["message"]
        
        result = api.load_database_file()
        assert result["status"] == "error"
        assert "Window not initialized" in result["message"]
        
        result = api.export_table_csv("test")
        assert result["status"] == "error"
        assert "Window not initialized" in result["message"]
        
        result = api.import_csv_table()
        assert result["status"] == "error"
        assert "Window not initialized" in result["message"]


class TestDesktopIntegration:
    """Integration tests for desktop features"""

    def test_full_workflow_save_load(self, tmp_path):
        """Test full workflow: create DB, save, load"""
        api = DesktopAPI()
        mock_window = MagicMock()
        api.set_window(mock_window)
        
        db = Database(name="workflow_db")
        schema = [{"name": "id", "type": "integer"}, {"name": "data", "type": "string"}]
        db.create_table("workflow_table", schema)
        db.insert_row("workflow_table", {"id": 1, "data": "test"})
        
        mock_state = MagicMock()
        mock_state.db_registry = {"workflow_db": db}
        mock_state.active_db_name = "workflow_db"
        
        save_path = str(tmp_path / "workflow.json")
        mock_window.create_file_dialog.return_value = save_path
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            save_result = api.save_database_file()
            assert save_result["status"] == "ok"
            assert Path(save_path).exists()
        
        mock_state.db_registry = {}
        mock_state.active_db_name = None
        mock_window.create_file_dialog.return_value = [save_path]
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            load_result = api.load_database_file()
            assert load_result["status"] == "ok"
            
            loaded_db_name = Path(save_path).stem
            assert loaded_db_name in mock_state.db_registry
            loaded_db = mock_state.db_registry[loaded_db_name]
            assert "workflow_table" in loaded_db.tables

    def test_full_workflow_csv_export_import(self, tmp_path):
        """Test full workflow: export CSV, import CSV"""
        api = DesktopAPI()
        mock_window = MagicMock()
        api.set_window(mock_window)
        
        db = Database(name="csv_db")
        schema = [{"name": "id", "type": "integer"}, {"name": "value", "type": "real"}]
        db.create_table("original_table", schema)
        db.insert_row("original_table", {"id": 1, "value": 10.5})
        db.insert_row("original_table", {"id": 2, "value": 20.3})
        
        mock_state = MagicMock()
        mock_state.db_registry = {"csv_db": db}
        mock_state.active_db_name = "csv_db"
        
        csv_path = str(tmp_path / "export.csv")
        mock_window.create_file_dialog.return_value = csv_path
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            export_result = api.export_table_csv("original_table")
            assert export_result["status"] == "ok"
            assert Path(csv_path).exists()
        
        mock_window.create_file_dialog.return_value = [csv_path]
        
        with patch('src.desktop.app.app') as mock_app:
            mock_app.state.app_state = mock_state
            
            import_result = api.import_csv_table()
            assert import_result["status"] == "ok"
            assert import_result["rows_imported"] == 2
            
            assert "export" in db.tables
            imported_table = db.tables["export"]
            assert len(imported_table.rows) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

