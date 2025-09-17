from __future__ import annotations

import json
import atexit
from pathlib import Path

import webview

from src.core.database import Database
from src.core.operations import union_tables


# Desktop app with persistence
class PersistentAPI:
    def __init__(self) -> None:
        self.storage_dir = Path("desktop_databases")
        self.storage_dir.mkdir(exist_ok=True)
        self.db_file = self.storage_dir / "desktop.json"
        
        # Load existing database or create new one
        if self.db_file.exists():
            try:
                self.db = Database.load(str(self.db_file))
                print(f"Loaded desktop database from {self.db_file}")
            except Exception as e:
                print(f"Warning: Could not load desktop database: {e}")
                self.db = Database(name="desktop")
        else:
            self.db = Database(name="desktop")
        
        # Auto-save on exit
        atexit.register(self._save_database)

    def _save_database(self) -> None:
        """Save database to file"""
        try:
            self.db.save(str(self.db_file))
            print(f"Desktop database saved to {self.db_file}")
        except Exception as e:
            print(f"Warning: Could not save desktop database: {e}")

    def _auto_save(self) -> None:
        """Auto-save after operations"""
        self._save_database()

    def create_table(self, name: str, schema_json: str) -> dict:
        schema = json.loads(schema_json)
        table = self.db.create_table(name, schema)
        self._auto_save()
        return table.to_json()

    def insert_row(self, table: str, values_json: str) -> dict:
        values = json.loads(values_json)
        self.db.insert_row(table, values)
        self._auto_save()
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
        self._auto_save()
        return res.to_json()

    def save(self, path: str) -> dict:
        file = path or str(Path.cwd() / "database.json")
        self.db.save(file)
        return {"path": file}

    def load(self, path: str) -> dict:
        file = path or str(Path.cwd() / "database.json")
        self.db = Database.load(file)
        self._auto_save()  # Save to persistent location
        return {"status": "ok"}

    def dump(self) -> dict:
        return self.db.to_json()

    def delete_table(self, name: str) -> dict:
        self.db.drop_table(name)
        self._auto_save()
        return {"status": "deleted", "name": name}


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>TDMS Desktop - Persistent Storage</title>
    <script src='https://cdn.tailwindcss.com'></script>
  </head>
  <body class='min-h-screen bg-slate-950 text-slate-100'>
    <header class='max-w-6xl mx-auto px-6 py-6'>
      <h1 class='text-3xl font-bold'>TDMS Desktop <span class='text-indigo-400'>· Persistent Storage</span></h1>
      <p class='text-slate-400'>Local database with automatic persistence.</p>
      <p class='text-green-400 text-sm'>✅ Data automatically saved to: desktop_databases/desktop.json</p>
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
            <button class='col-span-2 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700' onclick='pywebview.api.save(path.value).then(refresh)'>Export</button>
            <button class='col-span-2 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700' onclick='pywebview.api.load(path.value).then(refresh)'>Import</button>
          </div>
          <p class='text-xs text-slate-400 mt-2'>Note: Data is automatically saved. Export/Import for backup purposes.</p>
        </div>
      </section>
      <section class='col-span-12 lg:col-span-7'>
        <h2 class='text-xl font-semibold mb-3'>Database State</h2>
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


def main() -> None:
    api = PersistentAPI()
    window = webview.create_window("TDMS Desktop - Persistent", html=HTML, js_api=api, width=960, height=800)
    webview.start(debug=True)


if __name__ == "__main__":
    main()



