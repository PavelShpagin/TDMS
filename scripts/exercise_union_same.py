from __future__ import annotations

import json
import urllib.request


BASE = "http://127.0.0.1:8000"


def post(path: str, payload: dict) -> dict:
	data = json.dumps(payload).encode("utf-8")
	req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"})
	with urllib.request.urlopen(req, timeout=5) as r:
		return json.loads(r.read().decode("utf-8"))


def main() -> None:
	# Reset table X
	try:
		post("/delete_table", {"name": "X"})
	except Exception:
		pass

	# Create X(id:int,name:string)
	assert post("/create_table", {"name": "X", "schema": [
		{"name": "id", "type": "integer"},
		{"name": "name", "type": "string"},
	]})["status"] == "ok"

	# Insert two rows
	assert post("/insert_row", {"table": "X", "values": {"id": 1, "name": "A"}})["status"] == "ok"
	assert post("/insert_row", {"table": "X", "values": {"id": 2, "name": "B"}})["status"] == "ok"

	# Union X with X; expect deduped two rows
	u = post("/union", {"left": "X", "right": "X", "name": "XU"})
	rows = u["rows"]
	assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}: {rows}"
	print("UNION SAME OK")


if __name__ == "__main__":
	main()


