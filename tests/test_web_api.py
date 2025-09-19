from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.web.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_database(client):
    """Create a sample database with test data"""
    import uuid
    table_name = f"users_{str(uuid.uuid4())[:8]}"
    
    # Create a test table
    schema = [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}
    ]
    
    response = client.post("/create_table", json={
        "name": table_name,
        "schema": schema
    })
    assert response.status_code == 200
    
    # Insert test data
    test_users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Carol", "email": "carol@example.com"}
    ]
    
    for user in test_users:
        response = client.post("/insert_row", json={
            "table": table_name,
            "values": user
        })
        assert response.status_code == 200
    
    return table_name


# Basic API Tests
def test_index_page(client):
    """Test the main index page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Table Database" in response.text


def test_list_databases(client):
    """Test listing databases"""
    response = client.get("/databases")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert "databases" in data
    assert "default" in data["databases"]


def test_create_database(client):
    """Test creating a new database"""
    response = client.post("/create_database", json={"name": "test_db"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["active"] == "test_db"


def test_create_database_duplicate(client):
    """Test creating a database with duplicate name"""
    client.post("/create_database", json={"name": "test_db"})
    response = client.post("/create_database", json={"name": "test_db"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_switch_database(client):
    """Test switching between databases"""
    # Create a new database
    client.post("/create_database", json={"name": "test_db"})
    
    # Switch back to default
    response = client.post("/switch_database", json={"name": "default"})
    assert response.status_code == 200
    assert response.json()["active"] == "default"


def test_switch_nonexistent_database(client):
    """Test switching to nonexistent database"""
    response = client.post("/switch_database", json={"name": "nonexistent"})
    assert response.status_code == 400
    assert "Unknown database" in response.json()["detail"]


def test_delete_database(client):
    """Test deleting a database"""
    # Create a test database
    client.post("/create_database", json={"name": "to_delete"})
    
    # Delete it
    response = client.post("/delete_database", json={"name": "to_delete"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_delete_nonexistent_database(client):
    """Test deleting nonexistent database"""
    response = client.post("/delete_database", json={"name": "nonexistent"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_rename_database(client):
    """Test renaming a database"""
    # Create a test database
    client.post("/create_database", json={"name": "old_name"})
    
    # Rename it
    response = client.post("/rename_database", json={
        "old": "old_name",
        "new": "new_name"
    })
    assert response.status_code == 200
    assert response.json()["active"] == "new_name"


# Table API Tests
def test_create_table(client):
    """Test creating a table"""
    schema = [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ]
    
    response = client.post("/create_table", json={
        "name": "test_table",
        "schema": schema
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["table"]["name"] == "test_table"


def test_create_table_invalid_payload(client):
    """Test creating table with invalid payload"""
    response = client.post("/create_table", json={
        "name": "test_table"
        # Missing schema
    })
    assert response.status_code == 400
    assert "Invalid payload" in response.json()["detail"]


def test_insert_row(client, sample_database):
    """Test inserting a row"""
    response = client.post("/insert_row", json={
        "table": sample_database,
        "values": {"id": 4, "name": "Dave", "email": "dave@example.com"}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_insert_row_invalid_table(client):
    """Test inserting row into nonexistent table"""
    response = client.post("/insert_row", json={
        "table": "nonexistent",
        "values": {"id": 1, "name": "Test"}
    })
    assert response.status_code == 400


def test_list_tables(client, sample_database):
    """Test listing all tables"""
    response = client.get("/tables")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert len(data["tables"]) >= 1
    
    # Find our test table
    test_table = next((t for t in data["tables"] if t["name"] == sample_database), None)
    assert test_table is not None
    assert test_table["rowCount"] == 3


def test_view_table(client, sample_database):
    """Test viewing a specific table"""
    response = client.get(f"/view_table/{sample_database}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_database
    assert len(data["rows"]) == 3


def test_view_nonexistent_table(client):
    """Test viewing nonexistent table"""
    response = client.get("/view_table/nonexistent")
    assert response.status_code == 404


def test_delete_table(client, sample_database):
    """Test deleting a table"""
    response = client.post("/delete_table", json={"name": sample_database})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["name"] == sample_database


def test_delete_nonexistent_table(client):
    """Test deleting nonexistent table"""
    response = client.post("/delete_table", json={"name": "nonexistent"})
    assert response.status_code == 400


# Union Operation Tests
def test_union_tables(client):
    """Test union operation between two tables"""
    # Create first table
    schema1 = [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
    client.post("/create_table", json={"name": "table1", "schema": schema1})
    client.post("/insert_row", json={"table": "table1", "values": {"id": 1, "name": "Alice"}})
    client.post("/insert_row", json={"table": "table1", "values": {"id": 2, "name": "Bob"}})
    
    # Create second table
    schema2 = [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
    client.post("/create_table", json={"name": "table2", "schema": schema2})
    client.post("/insert_row", json={"table": "table2", "values": {"id": 3, "name": "Carol"}})
    client.post("/insert_row", json={"table": "table2", "values": {"id": 4, "name": "Dave"}})
    
    # Perform union
    response = client.post("/union", json={
        "left": "table1",
        "right": "table2",
        "name": "union_result"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "union_result"
    assert len(data["rows"]) == 4


def test_union_missing_tables(client):
    """Test union with missing table names"""
    response = client.post("/union", json={
        "left": "table1"
        # Missing right table
    })
    assert response.status_code == 400
    assert "Provide left and right table names" in response.json()["detail"]


def test_union_nonexistent_tables(client):
    """Test union with nonexistent tables"""
    response = client.post("/union", json={
        "left": "nonexistent1",
        "right": "nonexistent2"
    })
    assert response.status_code == 400


# Persistence Tests
def test_save_database(client, sample_database, tmp_path):
    """Test saving database to file"""
    file_path = str(tmp_path / "test_save.json")
    
    response = client.post("/save", json={
        "name": "default",
        "path": file_path
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert Path(file_path).exists()


def test_load_database(client, tmp_path):
    """Test loading database from file"""
    # First create and save a database
    schema = [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
    client.post("/create_table", json={"name": "test_table", "schema": schema})
    client.post("/insert_row", json={"table": "test_table", "values": {"id": 1, "name": "Test"}})
    
    file_path = str(tmp_path / "test_load.json")
    client.post("/save", json={"path": file_path})
    
    # Create a new database
    client.post("/create_database", json={"name": "empty_db"})
    
    # Load the saved database
    response = client.post("/load", json={
        "name": "loaded_db",
        "path": file_path
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["name"] == "loaded_db"


def test_import_database(client):
    """Test importing database from JSON data"""
    json_data = {
        "name": "imported_db",
        "tables": [
            {
                "name": "imported_table",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "value", "type": "string"}
                ],
                "rows": [
                    {"values": {"id": 1, "value": "test"}}
                ]
            }
        ]
    }
    
    response = client.post("/import_database", json={
        "name": "imported",
        "data": json_data
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["name"] == "imported"


def test_import_database_invalid_data(client):
    """Test importing database with invalid data"""
    response = client.post("/import_database", json={
        "name": "test",
        "data": "invalid_data"  # Should be dict
    })
    assert response.status_code == 400
    assert "Provide name and data" in response.json()["detail"]


# Error Handling Tests
def test_invalid_json_payload(client):
    """Test handling of invalid JSON payloads"""
    response = client.post("/create_table", json={})
    assert response.status_code == 400


def test_missing_required_fields(client):
    """Test handling of missing required fields"""
    response = client.post("/create_database", json={})
    assert response.status_code == 400
    assert "Provide database name" in response.json()["detail"]


# Integration Tests
def test_full_workflow(client):
    """Test a complete workflow: create DB, tables, insert data, union, save"""
    # Create new database
    response = client.post("/create_database", json={"name": "workflow_test"})
    assert response.status_code == 200
    
    # Create first table
    schema = [{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}]
    response = client.post("/create_table", json={"name": "employees", "schema": schema})
    assert response.status_code == 200
    
    # Create second table
    response = client.post("/create_table", json={"name": "contractors", "schema": schema})
    assert response.status_code == 200
    
    # Insert data into both tables
    employees = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    contractors = [
        {"id": 3, "name": "Carol"},
        {"id": 4, "name": "Dave"}
    ]
    
    for emp in employees:
        response = client.post("/insert_row", json={"table": "employees", "values": emp})
        assert response.status_code == 200
    
    for con in contractors:
        response = client.post("/insert_row", json={"table": "contractors", "values": con})
        assert response.status_code == 200
    
    # Perform union
    response = client.post("/union", json={
        "left": "employees",
        "right": "contractors",
        "name": "all_people"
    })
    assert response.status_code == 200
    union_data = response.json()
    assert len(union_data["rows"]) == 4
    
    # Verify final state
    response = client.get("/tables")
    assert response.status_code == 200
    tables = response.json()["tables"]
    assert len(tables) == 3  # employees, contractors, all_people
    
    # Find union table
    union_table = next(t for t in tables if t["name"] == "all_people")
    assert union_table["rowCount"] == 4


def test_concurrent_operations(client):
    """Test handling of concurrent-like operations"""
    # Create multiple tables rapidly
    for i in range(5):
        schema = [{"name": "id", "type": "integer"}, {"name": f"field_{i}", "type": "string"}]
        response = client.post("/create_table", json={
            "name": f"table_{i}",
            "schema": schema
        })
        assert response.status_code == 200
    
    # Verify all tables were created
    response = client.get("/tables")
    assert response.status_code == 200
    tables = response.json()["tables"]
    table_names = [t["name"] for t in tables]
    
    for i in range(5):
        assert f"table_{i}" in table_names
