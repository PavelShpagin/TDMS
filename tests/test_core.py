from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any, Dict

from src.core.database import Database
from src.core.operations import union_tables
from src.core.table import Table
from src.core.column import Column
from src.core.row import Row
from src.core.validator import TypeValidator


# Database Tests
def test_create_table_and_schema():
    db = Database(name="test")
    schema = [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "dob", "type": "date"},
        {"name": "active", "type": "char"},
        {"name": "membership", "type": "dateInvl"},
    ]
    t = db.create_table("users", schema)
    assert t.schema == [(c["name"], c["type"]) for c in schema]
    assert "users" in db.tables
    assert db.get_table("users") == t


def test_create_duplicate_table():
    db = Database(name="test")
    schema = [("id", "integer"), ("name", "string")]
    db.create_table("users", schema)
    
    with pytest.raises(ValueError, match="Table 'users' already exists"):
        db.create_table("users", schema)


def test_drop_table():
    db = Database(name="test")
    schema = [("id", "integer"), ("name", "string")]
    db.create_table("users", schema)
    
    assert "users" in db.tables
    db.drop_table("users")
    assert "users" not in db.tables


def test_drop_nonexistent_table():
    db = Database(name="test")
    
    with pytest.raises(ValueError, match="Table 'nonexistent' does not exist"):
        db.drop_table("nonexistent")


def test_get_nonexistent_table():
    db = Database(name="test")
    
    with pytest.raises(ValueError, match="Table 'nonexistent' does not exist"):
        db.get_table("nonexistent")


def test_insert_row_with_validation():
    db = Database(name="test")
    db.create_table(
        "events",
        [
            ("id", "integer"),
            ("title", "string"),
            ("when", "date"),
            ("period", "dateInvl"),
        ],
    )
    db.insert_row(
        "events",
        {"id": 1, "title": "Conference", "when": "2025-01-01", "period": {"start": "2025-01-01", "end": "2025-01-03"}},
    )
    t = db.get_table("events")
    assert len(t.rows) == 1
    assert t.rows[0].values["when"] == "2025-01-01"


def test_edit_row():
    db = Database(name="test")
    db.create_table("users", [("id", "integer"), ("name", "string")])
    db.insert_row("users", {"id": 1, "name": "Alice"})
    
    db.edit_row("users", 0, {"id": 1, "name": "Alice Updated"})
    
    table = db.get_table("users")
    assert table.rows[0].values["name"] == "Alice Updated"


def test_database_persistence(tmp_path: Path):
    # Create and save database
    db = Database(name="test_db")
    db.create_table("users", [("id", "integer"), ("name", "string")])
    db.insert_row("users", {"id": 1, "name": "Alice"})
    db.insert_row("users", {"id": 2, "name": "Bob"})
    
    file_path = tmp_path / "test_db.json"
    db.save(file_path)
    
    # Load database
    loaded_db = Database.load(file_path)
    
    assert loaded_db.name == "test_db"
    assert "users" in loaded_db.tables
    assert len(loaded_db.get_table("users").rows) == 2
    assert loaded_db.get_table("users").rows[0].values["name"] == "Alice"


def test_database_to_json():
    db = Database(name="test_db")
    db.create_table("users", [("id", "integer"), ("name", "string")])
    db.insert_row("users", {"id": 1, "name": "Alice"})
    
    json_data = db.to_json()
    
    assert json_data["name"] == "test_db"
    assert len(json_data["tables"]) == 1
    assert json_data["tables"][0]["name"] == "users"


def test_database_from_json():
    json_data = {
        "name": "test_db",
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"}
                ],
                "rows": [
                    {"id": 1, "name": "Alice"}
                ]
            }
        ]
    }
    
    db = Database.from_json(json_data)
    
    assert db.name == "test_db"
    assert "users" in db.tables
    assert len(db.get_table("users").rows) == 1
    assert db.get_table("users").rows[0].values["name"] == "Alice"


# Table Tests
def test_table_creation():
    schema = [("id", "integer"), ("name", "string"), ("active", "char")]
    table = Table.from_schema("test_table", schema)
    
    assert table.name == "test_table"
    assert len(table.columns) == 3
    assert table.schema == schema
    assert len(table.rows) == 0


def test_table_add_row():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    
    row = table.add_row({"id": 1, "name": "Alice"})
    
    assert len(table.rows) == 1
    assert row.values["id"] == 1
    assert row.values["name"] == "Alice"


def test_table_update_row():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    table.add_row({"id": 1, "name": "Alice"})
    
    updated_row = table.update_row(0, {"id": 1, "name": "Alice Updated"})
    
    assert updated_row.values["name"] == "Alice Updated"
    assert table.rows[0].values["name"] == "Alice Updated"


def test_table_update_row_invalid_index():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    
    with pytest.raises(IndexError, match="Row index out of range"):
        table.update_row(0, {"id": 1, "name": "Alice"})


def test_table_get_rows():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    table.add_row({"id": 1, "name": "Alice"})
    table.add_row({"id": 2, "name": "Bob"})
    
    rows = table.get_rows()
    
    assert len(rows) == 2
    assert rows[0] == {"id": 1, "name": "Alice"}
    assert rows[1] == {"id": 2, "name": "Bob"}


def test_table_schema_signature():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    
    signature = table.schema_signature()
    
    assert signature == (("id", "integer"), ("name", "string"))


def test_table_to_json():
    table = Table.from_schema("users", [("id", "integer"), ("name", "string")])
    table.add_row({"id": 1, "name": "Alice"})
    
    json_data = table.to_json()
    
    assert json_data["name"] == "users"
    assert len(json_data["columns"]) == 2
    assert len(json_data["rows"]) == 1
    assert json_data["rows"][0]["name"] == "Alice"


def test_table_from_json():
    json_data = {
        "name": "users",
        "columns": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"}
        ],
        "rows": [
            {"id": 1, "name": "Alice"}
        ]
    }
    
    table = Table.from_json(json_data)
    
    assert table.name == "users"
    assert len(table.columns) == 2
    assert len(table.rows) == 1
    assert table.rows[0].values["name"] == "Alice"


# Union Operation Tests
def test_union_operation():
    db = Database(name="test")
    schema = [("id", "integer"), ("name", "string")]
    t1 = db.create_table("t1", schema)
    t2 = db.create_table("t2", schema)

    db.insert_row("t1", {"id": 1, "name": "Alice"})
    db.insert_row("t1", {"id": 2, "name": "Bob"})
    db.insert_row("t2", {"id": 2, "name": "Bob"})
    db.insert_row("t2", {"id": 3, "name": "Carol"})

    res = union_tables(t1, t2)
    rows = sorted(res.get_rows(), key=lambda r: r["id"])
    assert len(rows) == 4  # UNION ALL semantics - includes duplicates
    assert [r["id"] for r in rows] == [1, 2, 2, 3]


def test_union_different_schemas():
    t1 = Table.from_schema("t1", [("id", "integer"), ("name", "string")])
    t2 = Table.from_schema("t2", [("id", "integer"), ("age", "integer")])
    
    t1.add_row({"id": 1, "name": "Alice"})
    t2.add_row({"id": 2, "age": 25})
    
    result = union_tables(t1, t2)
    
    assert result.schema == [("id", "integer"), ("name", "string"), ("age", "integer")]
    rows = result.get_rows()
    assert len(rows) == 2
    assert rows[0] == {"id": 1, "name": "Alice", "age": None}
    assert rows[1] == {"id": 2, "name": None, "age": 25}


def test_union_incompatible_types():
    t1 = Table.from_schema("t1", [("id", "integer"), ("value", "string")])
    t2 = Table.from_schema("t2", [("id", "integer"), ("value", "integer")])
    
    with pytest.raises(ValueError, match="Incompatible schemas"):
        union_tables(t1, t2)


def test_union_empty_tables():
    t1 = Table.from_schema("t1", [("id", "integer"), ("name", "string")])
    t2 = Table.from_schema("t2", [("id", "integer"), ("name", "string")])
    
    result = union_tables(t1, t2)
    
    assert len(result.rows) == 0
    assert result.schema == [("id", "integer"), ("name", "string")]


# Column Tests
def test_column_creation():
    column = Column("id", "integer")
    
    assert column.name == "id"
    assert column.type_name == "integer"


def test_column_to_json():
    column = Column("name", "string")
    
    json_data = column.to_json()
    
    assert json_data == {"name": "name", "type": "string"}


def test_column_from_json():
    json_data = {"name": "age", "type": "integer"}
    
    column = Column.from_json(json_data)
    
    assert column.name == "age"
    assert column.type_name == "integer"


# Row Tests
def test_row_creation():
    values = {"id": 1, "name": "Alice", "active": True}
    row = Row(values=values)
    
    assert row.values == values


def test_row_to_json():
    values = {"id": 1, "name": "Alice"}
    row = Row(values=values)
    
    json_data = row.to_json()
    
    assert json_data == values


def test_row_from_json():
    json_data = {"id": 2, "name": "Bob"}
    
    row = Row.from_json(json_data)
    
    assert row.values == {"id": 2, "name": "Bob"}


# Validator Tests
def test_type_validator_integer():
    schema = [("id", "integer")]
    
    # Valid integer
    result = TypeValidator.validate_row(schema, {"id": 42})
    assert result["id"] == 42
    
    # String that can be converted to integer
    result = TypeValidator.validate_row(schema, {"id": "123"})
    assert result["id"] == 123
    
    # Invalid integer
    with pytest.raises(ValueError):
        TypeValidator.validate_row(schema, {"id": "not_a_number"})


def test_type_validator_string():
    schema = [("name", "string")]
    
    # Valid string
    result = TypeValidator.validate_row(schema, {"name": "Alice"})
    assert result["name"] == "Alice"
    
    # Number converted to string
    result = TypeValidator.validate_row(schema, {"name": 123})
    assert result["name"] == "123"


def test_type_validator_char():
    schema = [("status", "char")]
    
    # Valid single character
    result = TypeValidator.validate_row(schema, {"status": "A"})
    assert result["status"] == "A"
    
    # Invalid multi-character string should raise error
    with pytest.raises(ValueError, match="Char must be exactly one character"):
        TypeValidator.validate_row(schema, {"status": "Active"})


def test_type_validator_date():
    schema = [("birth_date", "date")]
    
    # Valid date string
    result = TypeValidator.validate_row(schema, {"birth_date": "2023-12-25"})
    assert result["birth_date"] == "2023-12-25"


def test_type_validator_date_interval():
    schema = [("period", "dateInvl")]
    
    # Valid date interval
    interval = {"start": "2023-01-01", "end": "2023-12-31"}
    result = TypeValidator.validate_row(schema, {"period": interval})
    assert result["period"] == interval


def test_type_validator_missing_column():
    schema = [("id", "integer"), ("name", "string")]
    
    # Missing required column should raise error
    with pytest.raises(ValueError, match="Missing value for column 'name'"):
        TypeValidator.validate_row(schema, {"id": 1})


def test_type_validator_extra_column():
    schema = [("id", "integer")]
    
    # Extra columns should raise error
    with pytest.raises(ValueError, match="Unexpected columns"):
        TypeValidator.validate_row(schema, {"id": 1, "extra": "ignored"})


# Integration Tests
def test_full_workflow():
    """Test a complete workflow with database, tables, and operations"""
    db = Database(name="company")
    
    # Create employees table
    employees_schema = [
        ("id", "integer"),
        ("name", "string"),
        ("department", "string"),
        ("hire_date", "date")
    ]
    employees = db.create_table("employees", employees_schema)
    
    # Create contractors table
    contractors_schema = [
        ("id", "integer"),
        ("name", "string"),
        ("company", "string"),
        ("start_date", "date")
    ]
    contractors = db.create_table("contractors", contractors_schema)
    
    # Add data
    db.insert_row("employees", {"id": 1, "name": "Alice", "department": "Engineering", "hire_date": "2023-01-15"})
    db.insert_row("employees", {"id": 2, "name": "Bob", "department": "Marketing", "hire_date": "2023-02-01"})
    
    db.insert_row("contractors", {"id": 3, "name": "Carol", "company": "TechCorp", "start_date": "2023-03-01"})
    db.insert_row("contractors", {"id": 4, "name": "Dave", "company": "DevCorp", "start_date": "2023-04-01"})
    
    # Test union operation
    all_people = union_tables(employees, contractors)
    
    assert len(all_people.rows) == 4
    assert all_people.schema == [
        ("id", "integer"),
        ("name", "string"),
        ("department", "string"),
        ("hire_date", "date"),
        ("company", "string"),
        ("start_date", "date")
    ]
    
    # Verify data integrity
    rows = all_people.get_rows()
    alice_row = next(r for r in rows if r["name"] == "Alice")
    assert alice_row["department"] == "Engineering"
    assert alice_row["company"] is None  # Not in contractors table
    
    carol_row = next(r for r in rows if r["name"] == "Carol")
    assert carol_row["company"] == "TechCorp"
    assert carol_row["department"] is None  # Not in employees table


