from __future__ import annotations

from pathlib import Path

from src.core.database import Database
from src.core.operations import union_tables


def test_create_table_and_schema(tmp_path: Path):
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


def test_insert_row_with_validation(tmp_path: Path):
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


def test_union_operation(tmp_path: Path):
    db = Database(name="test")
    schema = [("id", "integer"), ("name", "string")]
    t1 = db.create_table("t1", schema)
    t2 = db.create_table("t2", schema)

    db.insert_row("t1", {"id": 1, "name": "Alice"})
    db.insert_row("t1", {"id": 2, "name": "Bob"})
    db.insert_row("t2", {"id": 2, "name": "Bob"})
    db.insert_row("t2", {"id": 3, "name": "Carol"})

    res = union_tables(t1, t2)
    rows = sorted(res.get_rows(), key=lambda r: r["id"])  # unique 1,2,3
    assert [r["id"] for r in rows] == [1, 2, 3]


