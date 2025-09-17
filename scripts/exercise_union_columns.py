from __future__ import annotations

import json
import urllib.request


BASE = "http://127.0.0.1:8000"


def post(path: str, payload: dict) -> dict:
	data = json.dumps(payload).encode("utf-8")
	req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
	with urllib.request.urlopen(req, timeout=5) as r:
		return json.loads(r.read().decode("utf-8"))


def get(path: str) -> dict:
	with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as r:
		return json.loads(r.read().decode("utf-8"))


def main() -> None:
	# Clean slate: try delete if exists
	for name in ("A", "B", "U"):
		try:
			post("/delete_table", {"name": name})
		except Exception:
			pass

	# Create A(id:int, name:string) and B(id:int, age:integer)
	assert post("/create_table", {"name": "A", "schema": [
		{"name": "id", "type": "integer"},
		{"name": "name", "type": "string"},
	]})["status"] == "ok"
	assert post("/create_table", {"name": "B", "schema": [
		{"name": "id", "type": "integer"},
		{"name": "age", "type": "integer"},
	]})["status"] == "ok"

	# Insert rows
	assert post("/insert_row", {"table": "A", "values": {"id": 1, "name": "Alice"}})["status"] == "ok"
	assert post("/insert_row", {"table": "B", "values": {"id": 2, "age": 30}})["status"] == "ok"

	# Union
	u = post("/union", {"left": "A", "right": "B", "name": "U"})

	# Expect combined columns: id, name, age
	cols = [c["name"] for c in u["columns"]]
	assert cols == ["id", "name", "age"], f"Bad columns: {cols}"

	# Expect two rows with nulls appropriately
	rows = u["rows"]
	assert any(r == {"id": 1, "name": "Alice", "age": None} for r in rows)
	assert any(r == {"id": 2, "name": None, "age": 30} for r in rows)

	print("UNION COLUMNS OK")


if __name__ == "__main__":
	main()


