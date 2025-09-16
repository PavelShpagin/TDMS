from __future__ import annotations

import os
import sys

# Ensure project root is on sys.path so 'src' package is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.desktop.app import API


def main() -> None:
    api = API()
    api.create_table("A", "[{\"name\":\"id\",\"type\":\"integer\"},{\"name\":\"name\",\"type\":\"string\"}]")
    api.create_table("B", "[{\"name\":\"id\",\"type\":\"integer\"},{\"name\":\"name\",\"type\":\"string\"}]")
    api.insert_row("A", "{\"id\":1,\"name\":\"Alice\"}")
    api.insert_row("A", "{\"id\":2,\"name\":\"Bob\"}")
    api.insert_row("B", "{\"id\":2,\"name\":\"Bob\"}")
    api.insert_row("B", "{\"id\":3,\"name\":\"Carol\"}")
    res = api.union("A", "B")
    name = res["name"]
    assert len(api.db.get_table(name).rows) == 3
    print("DESKTOP API OK")


if __name__ == "__main__":
    main()
