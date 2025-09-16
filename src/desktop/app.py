from __future__ import annotations

import json
from pathlib import Path

import webview

from src.core.database import Database
from src.core.operations import union_tables


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset='utf-8'>
    <title>TDMS Desktop - Variant 58</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 16px; }
      textarea, input, button { margin: 4px; }
      pre { background: #f5f5f5; padding: 8px; }
      .row { display:flex; gap:8px; align-items:center; }
    </style>
  </head>
  <body>
    <h1>TDMS Desktop - Variant 58</h1>

    <h2>Create Table</h2>
    <div>
      <input id="tname" placeholder="table name" />
      <textarea id="schema" rows="3" cols="60" placeholder='[{"name":"id","type":"integer"}]'></textarea>
      <button onclick="pywebview.api.create_table(tname.value, schema.value).then(refresh)">Create</button>
    </div>

    <h2>Insert Row</h2>
    <div>
      <input id="rtname" placeholder="table name" />
      <textarea id="values" rows="3" cols="60" placeholder='{"id":1}'></textarea>
      <button onclick="pywebview.api.insert_row(rtname.value, values.value).then(refresh)">Insert</button>
    </div>

    <h2>Union</h2>
    <div class="row">
      <input id="left" placeholder="left table" />
      <input id="right" placeholder="right table" />
      <button onclick="pywebview.api.union(left.value, right.value).then(refresh)">Union</button>
    </div>

    <h2>Persistence</h2>
    <div class="row">
      <input id="path" placeholder="database.json" />
      <button onclick="pywebview.api.save(path.value).then(refresh)">Save</button>
      <button onclick="pywebview.api.load(path.value).then(refresh)">Load</button>
    </div>

    <h2>State</h2>
    <pre id="state"></pre>

    <script>
      async function refresh(){
        const state = await pywebview.api.dump();
        document.getElementById('state').innerText = JSON.stringify(state, null, 2);
      }
      refresh();
    </script>
  </body>
 </html>
"""


class API:
    def __init__(self) -> None:
        self.db = Database(name="desktop")

    def create_table(self, name: str, schema_json: str) -> dict:
        schema = json.loads(schema_json)
        table = self.db.create_table(name, schema)
        return table.to_json()

    def insert_row(self, table: str, values_json: str) -> dict:
        values = json.loads(values_json)
        self.db.insert_row(table, values)
        return {"status": "ok"}

    def union(self, left: str, right: str) -> dict:
        t1 = self.db.get_table(left)
        t2 = self.db.get_table(right)
        res = union_tables(t1, t2)
        name = res.name
        i = 1
        while name in self.db.tables:
            i += 1
            name = f"{res.name}_{i}"
        res.name = name
        self.db.tables[name] = res
        return res.to_json()

    def save(self, path: str) -> dict:
        file = path or str(Path.cwd() / "database.json")
        self.db.save(file)
        return {"path": file}

    def load(self, path: str) -> dict:
        file = path or str(Path.cwd() / "database.json")
        self.db = Database.load(file)
        return {"status": "ok"}

    def dump(self) -> dict:
        return self.db.to_json()


def main() -> None:
    api = API()
    window = webview.create_window("TDMS Desktop - Variant 58", html=HTML, js_api=api, width=960, height=800)
    webview.start(debug=True)


if __name__ == "__main__":
    main()


