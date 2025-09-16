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
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>TDMS Desktop - Variant 58</title>
    <script src='https://cdn.tailwindcss.com'></script>
  </head>
  <body class='min-h-screen bg-slate-950 text-slate-100'>
    <header class='max-w-6xl mx-auto px-6 py-6'>
      <h1 class='text-3xl font-bold'>TDMS Desktop <span class='text-indigo-400'>· Variant 58</span></h1>
      <p class='text-slate-400'>Local database with union operation.</p>
    </header>
    <main class='max-w-6xl mx-auto px-6 grid grid-cols-12 gap-6 pb-16'>
      <section class='col-span-12 lg:col-span-5 space-y-6'>
        <div class='rounded-2xl border border-slate-800 bg-slate-900/60 p-5'>
          <h2 class='text-xl font-semibold'>Create Table</h2>
          <div class='mt-4 space-y-3'>
            <input id='tname' class='w-full px-3 py-2 rounded bg-slate-800/60 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500' placeholder='table name'>
            <textarea id='schema' rows='3' class='w-full px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='[{"name":"id","type":"integer"}]'></textarea>
            <button class='px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-white' onclick='pywebview.api.create_table(tname.value, schema.value).then(refresh)'>Create</button>
          </div>
        </div>
        <div class='rounded-2xl border border-slate-800 bg-slate-900/60 p-5'>
          <h2 class='text-xl font-semibold'>Insert Row</h2>
          <div class='mt-4 space-y-3'>
            <input id='rtname' class='w-full px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='table name'>
            <textarea id='values' rows='3' class='w-full px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='{"id":1}'></textarea>
            <button class='px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white' onclick='pywebview.api.insert_row(rtname.value, values.value).then(refresh)'>Insert</button>
          </div>
        </div>
        <div class='rounded-2xl border border-slate-800 bg-slate-900/60 p-5'>
          <h2 class='text-xl font-semibold'>Union</h2>
          <div class='mt-4 grid grid-cols-12 gap-3'>
            <input id='left' class='col-span-5 px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='left table'>
            <input id='right' class='col-span-5 px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='right table'>
            <div class='col-span-2'>
              <button class='w-full px-4 py-2 rounded bg-fuchsia-600 hover:bg-fuchsia-500 text-white' onclick='pywebview.api.union(left.value, right.value).then(refresh)'>Go</button>
            </div>
          </div>
        </div>
        <div class='rounded-2xl border border-slate-800 bg-slate-900/60 p-5'>
          <h2 class='text-xl font-semibold'>Persistence</h2>
          <div class='mt-4 grid grid-cols-12 gap-3'>
            <input id='path' class='col-span-8 px-3 py-2 rounded bg-slate-800/60 border border-slate-700' placeholder='database.json'>
            <button class='col-span-2 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700' onclick='pywebview.api.save(path.value).then(refresh)'>Save</button>
            <button class='col-span-2 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700' onclick='pywebview.api.load(path.value).then(refresh)'>Load</button>
          </div>
        </div>
      </section>
      <section class='col-span-12 lg:col-span-7'>
        <h2 class='text-xl font-semibold mb-3'>State</h2>
        <pre id='state' class='rounded-xl border border-slate-800 bg-slate-950/80 p-4 overflow-auto text-sm'></pre>
      </section>
    </main>
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

    def delete_table(self, name: str) -> dict:
        self.db.drop_table(name)
        return {"status": "deleted", "name": name}


def main() -> None:
    api = API()
    window = webview.create_window("TDMS Desktop - Variant 58", html=HTML, js_api=api, width=960, height=800)
    webview.start(debug=True)


if __name__ == "__main__":
    main()


