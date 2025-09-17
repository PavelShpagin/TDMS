from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.desktop.app import API


@pytest.fixture
def api():
    """Create a fresh API instance for each test"""
    return API()


def test_api_initialization(api):
    """Test API initializes with empty database"""
    state = api.dump()
    assert state["name"] == "desktop"
    assert state["tables"] == []


def test_create_table(api):
    """Test creating a table through the API"""
    schema_json = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ])
    
    result = api.create_table("users", schema_json)
    
    assert result["name"] == "users"
    assert len(result["columns"]) == 2
    assert result["columns"][0]["name"] == "id"
    assert result["columns"][1]["name"] == "name"


def test_create_table_invalid_json(api):
    """Test creating table with invalid JSON schema"""
    with pytest.raises(json.JSONDecodeError):
        api.create_table("users", "invalid json")


def test_insert_row(api):
    """Test inserting a row through the API"""
    # First create a table
    schema_json = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ])
    api.create_table("users", schema_json)
    
    # Insert a row
    values_json = json.dumps({"id": 1, "name": "Alice"})
    result = api.insert_row("users", values_json)
    
    assert result["status"] == "ok"
    
    # Verify the row was inserted
    state = api.dump()
    users_table = next(t for t in state["tables"] if t["name"] == "users")
    assert len(users_table["rows"]) == 1
    assert users_table["rows"][0]["name"] == "Alice"


def test_insert_row_invalid_json(api):
    """Test inserting row with invalid JSON values"""
    schema_json = json.dumps([{"name": "id", "type": "integer"}])
    api.create_table("test", schema_json)
    
    with pytest.raises(json.JSONDecodeError):
        api.insert_row("test", "invalid json")


def test_insert_row_nonexistent_table(api):
    """Test inserting row into nonexistent table"""
    values_json = json.dumps({"id": 1})
    
    with pytest.raises(ValueError):
        api.insert_row("nonexistent", values_json)


def test_union_operation(api):
    """Test union operation through the API"""
    # Create first table
    schema_json = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ])
    api.create_table("table1", schema_json)
    api.insert_row("table1", json.dumps({"id": 1, "name": "Alice"}))
    api.insert_row("table1", json.dumps({"id": 2, "name": "Bob"}))
    
    # Create second table
    api.create_table("table2", schema_json)
    api.insert_row("table2", json.dumps({"id": 3, "name": "Carol"}))
    api.insert_row("table2", json.dumps({"id": 4, "name": "Dave"}))
    
    # Perform union
    result = api.union("table1", "table2")
    
    assert result["name"] == "table1_UNION_table2"
    assert len(result["rows"]) == 4
    
    # Verify union table was added to database
    state = api.dump()
    union_table = next(t for t in state["tables"] if t["name"] == "table1_UNION_table2")
    assert union_table is not None


def test_union_duplicate_names(api):
    """Test union operation with duplicate result names"""
    # Create tables and perform first union
    schema_json = json.dumps([{"name": "id", "type": "integer"}])
    api.create_table("t1", schema_json)
    api.create_table("t2", schema_json)
    api.union("t1", "t2")  # Creates "t1_UNION_t2"
    
    # Create more tables and perform second union
    api.create_table("t3", schema_json)
    api.create_table("t4", schema_json)
    result = api.union("t1", "t2")  # Should create "t1_UNION_t2_2"
    
    assert result["name"] == "t1_UNION_t2_2"


def test_union_nonexistent_tables(api):
    """Test union with nonexistent tables"""
    with pytest.raises(ValueError):
        api.union("nonexistent1", "nonexistent2")


def test_save_database(api, tmp_path):
    """Test saving database to file"""
    # Create some test data
    schema_json = json.dumps([{"name": "id", "type": "integer"}])
    api.create_table("test", schema_json)
    api.insert_row("test", json.dumps({"id": 1}))
    
    # Save to file
    file_path = str(tmp_path / "test_save.json")
    result = api.save(file_path)
    
    assert result["path"] == file_path
    assert Path(file_path).exists()
    
    # Verify file contents
    with open(file_path, 'r') as f:
        data = json.load(f)
    assert data["name"] == "desktop"
    assert len(data["tables"]) == 1


def test_save_database_default_path(api):
    """Test saving database with default path"""
    result = api.save("")
    
    expected_path = str(Path.cwd() / "database.json")
    assert result["path"] == expected_path


def test_load_database(api, tmp_path):
    """Test loading database from file"""
    # Create test data file
    test_data = {
        "name": "loaded_db",
        "tables": [
            {
                "name": "loaded_table",
                "columns": [{"name": "id", "type": "integer"}],
                "rows": [{"id": 42}]
            }
        ]
    }
    
    file_path = tmp_path / "test_load.json"
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    # Load the database
    result = api.load(str(file_path))
    
    assert result["status"] == "ok"
    
    # Verify the data was loaded
    state = api.dump()
    assert state["name"] == "loaded_db"
    assert len(state["tables"]) == 1
    assert state["tables"][0]["name"] == "loaded_table"
    assert state["tables"][0]["rows"][0]["id"] == 42


def test_load_database_default_path(api):
    """Test loading database with default path"""
    # This should raise FileNotFoundError if file doesn't exist
    with pytest.raises(FileNotFoundError):
        api.load("nonexistent_default.json")


def test_load_nonexistent_file(api):
    """Test loading nonexistent file"""
    with pytest.raises(FileNotFoundError):
        api.load("nonexistent.json")


def test_dump_database(api):
    """Test dumping database state"""
    # Create some test data
    schema_json = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ])
    api.create_table("users", schema_json)
    api.insert_row("users", json.dumps({"id": 1, "name": "Alice"}))
    api.insert_row("users", json.dumps({"id": 2, "name": "Bob"}))
    
    # Dump the state
    state = api.dump()
    
    assert state["name"] == "desktop"
    assert len(state["tables"]) == 1
    assert state["tables"][0]["name"] == "users"
    assert len(state["tables"][0]["rows"]) == 2


def test_delete_table(api):
    """Test deleting a table"""
    # Create a table
    schema_json = json.dumps([{"name": "id", "type": "integer"}])
    api.create_table("to_delete", schema_json)
    
    # Verify it exists
    state = api.dump()
    assert len(state["tables"]) == 1
    
    # Delete it
    result = api.delete_table("to_delete")
    
    assert result["status"] == "deleted"
    assert result["name"] == "to_delete"
    
    # Verify it's gone
    state = api.dump()
    assert len(state["tables"]) == 0


def test_delete_nonexistent_table(api):
    """Test deleting nonexistent table"""
    with pytest.raises(ValueError):
        api.delete_table("nonexistent")


def test_complex_workflow(api, tmp_path):
    """Test a complex workflow with multiple operations"""
    # Create employees table
    employees_schema = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "department", "type": "string"}
    ])
    api.create_table("employees", employees_schema)
    
    # Add employees
    employees_data = [
        {"id": 1, "name": "Alice", "department": "Engineering"},
        {"id": 2, "name": "Bob", "department": "Marketing"}
    ]
    for emp in employees_data:
        api.insert_row("employees", json.dumps(emp))
    
    # Create contractors table
    contractors_schema = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "company", "type": "string"}
    ])
    api.create_table("contractors", contractors_schema)
    
    # Add contractors
    contractors_data = [
        {"id": 3, "name": "Carol", "company": "TechCorp"},
        {"id": 4, "name": "Dave", "company": "DevCorp"}
    ]
    for con in contractors_data:
        api.insert_row("contractors", json.dumps(con))
    
    # Perform union
    union_result = api.union("employees", "contractors")
    assert len(union_result["rows"]) == 4
    
    # Save to file
    file_path = str(tmp_path / "complex_workflow.json")
    save_result = api.save(file_path)
    assert Path(file_path).exists()
    
    # Create new API instance and load
    new_api = API()
    load_result = new_api.load(file_path)
    assert load_result["status"] == "ok"
    
    # Verify all data is preserved
    final_state = new_api.dump()
    assert len(final_state["tables"]) == 3  # employees, contractors, union
    
    # Find union table
    union_table = next(t for t in final_state["tables"] if "UNION" in t["name"])
    assert len(union_table["rows"]) == 4
    
    # Verify data integrity
    union_rows = union_table["rows"]
    alice_row = next(r for r in union_rows if r["name"] == "Alice")
    assert alice_row["department"] == "Engineering"
    assert alice_row["company"] is None
    
    carol_row = next(r for r in union_rows if r["name"] == "Carol")
    assert carol_row["company"] == "TechCorp"
    assert carol_row["department"] is None


def test_error_handling(api):
    """Test various error conditions"""
    # Test creating table with duplicate name
    schema_json = json.dumps([{"name": "id", "type": "integer"}])
    api.create_table("test", schema_json)
    
    with pytest.raises(ValueError, match="already exists"):
        api.create_table("test", schema_json)
    
    # Test invalid schema format
    with pytest.raises((json.JSONDecodeError, TypeError)):
        api.create_table("invalid", "not json")
    
    # Test inserting into nonexistent table
    with pytest.raises(ValueError):
        api.insert_row("nonexistent", json.dumps({"id": 1}))
    
    # Test union with nonexistent tables
    with pytest.raises(ValueError):
        api.union("nonexistent1", "nonexistent2")


def test_type_validation_through_api(api):
    """Test type validation works through the API"""
    # Create table with various types
    schema_json = json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "active", "type": "char"},
        {"name": "birth_date", "type": "date"}
    ])
    api.create_table("users", schema_json)
    
    # Insert valid data
    values_json = json.dumps({
        "id": "123",  # String that can be converted to int
        "name": "Alice",
        "active": "Y",
        "birth_date": "1990-01-01"
    })
    result = api.insert_row("users", values_json)
    assert result["status"] == "ok"
    
    # Verify type conversion happened
    state = api.dump()
    user_row = state["tables"][0]["rows"][0]
    assert user_row["id"] == 123  # Converted to integer
    assert user_row["name"] == "Alice"
    assert user_row["active"] == "Y"
    assert user_row["birth_date"] == "1990-01-01"


def test_persistence_roundtrip(api, tmp_path):
    """Test complete save/load roundtrip preserves all data"""
    # Create complex database structure
    api.create_table("table1", json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "data", "type": "string"}
    ]))
    
    api.create_table("table2", json.dumps([
        {"name": "id", "type": "integer"},
        {"name": "value", "type": "integer"}
    ]))
    
    # Add data with various types
    api.insert_row("table1", json.dumps({"id": 1, "data": "test"}))
    api.insert_row("table2", json.dumps({"id": 2, "value": 42}))
    
    # Perform union
    api.union("table1", "table2")
    
    # Save original state
    original_state = api.dump()
    file_path = str(tmp_path / "roundtrip.json")
    api.save(file_path)
    
    # Load into new API instance
    new_api = API()
    new_api.load(file_path)
    loaded_state = new_api.dump()
    
    # Compare states (should be identical)
    assert loaded_state["name"] == original_state["name"]
    assert len(loaded_state["tables"]) == len(original_state["tables"])
    
    # Sort tables by name for consistent comparison
    orig_tables = sorted(original_state["tables"], key=lambda t: t["name"])
    loaded_tables = sorted(loaded_state["tables"], key=lambda t: t["name"])
    
    for orig, loaded in zip(orig_tables, loaded_tables):
        assert orig["name"] == loaded["name"]
        assert orig["columns"] == loaded["columns"]
        assert orig["rows"] == loaded["rows"]
