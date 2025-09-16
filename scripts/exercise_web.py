from __future__ import annotations

import json
import time
import urllib.error
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


def wait_ready(retries: int = 20, delay: float = 0.25) -> None:
    for _ in range(retries):
        try:
            # index should return HTML; just check 200
            urllib.request.urlopen(BASE + "/", timeout=1).read(1)
            return
        except Exception:
            time.sleep(delay)
    raise RuntimeError("Server not reachable on 127.0.0.1:8000")


def main() -> None:
    wait_ready()
    # create tables
    print("create A", post("/create_table", {"name": "A", "schema": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ]}))
    print("create B", post("/create_table", {"name": "B", "schema": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"}
    ]}))
    # inserts
    print("insert A1", post("/insert_row", {"table": "A", "values": {"id": 1, "name": "Alice"}}))
    print("insert A2", post("/insert_row", {"table": "A", "values": {"id": 2, "name": "Bob"}}))
    print("insert B2", post("/insert_row", {"table": "B", "values": {"id": 2, "name": "Bob"}}))
    print("insert B3", post("/insert_row", {"table": "B", "values": {"id": 3, "name": "Carol"}}))
    # union
    res = post("/union", {"left": "A", "right": "B"})
    assert len(res["rows"]) == 3, "Union expected 3 unique rows"
    # view
    vt = get("/view_table/" + res["name"])
    assert len(vt["rows"]) == 3
    print("WEB OK")


if __name__ == "__main__":
    main()



