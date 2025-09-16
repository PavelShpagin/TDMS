from __future__ import annotations

import json
import urllib.request


BASE = "http://127.0.0.1:8000"


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> None:
    # Clean slate: try delete if exists
    try:
        post("/delete_table", {"name": "A"})
    except Exception:
        pass
    try:
        post("/delete_table", {"name": "B"})
    except Exception:
        pass

    # Create
    assert post("/create_table", {"name": "A", "schema": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ]})["status"] == "ok"
    assert post("/create_table", {"name": "B", "schema": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ]})["status"] == "ok"

    # Insert
    for payload in [
        ("A", {"id": 1, "name": "Alice"}),
        ("A", {"id": 2, "name": "Bob"}),
        ("B", {"id": 2, "name": "Bob"}),
        ("B", {"id": 3, "name": "Carol"}),
    ]:
        assert post("/insert_row", {"table": payload[0], "values": payload[1]})["status"] == "ok"

    # View
    a = get("/view_table/A")
    b = get("/view_table/B")
    assert len(a["rows"]) == 2 and len(b["rows"]) == 2

    # Union
    u = post("/union", {"left": "A", "right": "B"})
    assert len(u["rows"]) == 3

    # Delete
    assert post("/delete_table", {"name": "A"})["status"] == "deleted"
    assert post("/delete_table", {"name": "B"})["status"] == "deleted"

    print("WEB FULL OK")


if __name__ == "__main__":
    main()


