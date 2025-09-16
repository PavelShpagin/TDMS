from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .table import Table


@dataclass
class Database:
    name: str
    tables: Dict[str, Table] = field(default_factory=dict)

    def create_table(self, name: str, schema: Iterable[Tuple[str, str]] | List[Dict[str, str]]) -> Table:
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")

        normalized_schema: List[Tuple[str, str]] = []
        seen: set[str] = set()
        for item in schema:
            if isinstance(item, tuple):
                col_name, type_name = item
            elif isinstance(item, dict):
                col_name, type_name = item["name"], item["type"]
            else:
                raise ValueError("Invalid schema element; expected tuple or dict")
            col_name = str(col_name)
            if col_name in seen:
                raise ValueError(f"Duplicate column name '{col_name}'")
            seen.add(col_name)
            normalized_schema.append((col_name, type_name))

        table = Table.from_schema(name, normalized_schema)
        self.tables[name] = table
        return table

    def drop_table(self, name: str) -> None:
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        del self.tables[name]

    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise ValueError(f"Table '{name}' does not exist")
        return self.tables[name]

    def insert_row(self, table_name: str, values: Dict[str, Any]) -> None:
        self.get_table(table_name).add_row(values)

    def edit_row(self, table_name: str, index: int, values: Dict[str, Any]) -> None:
        self.get_table(table_name).update_row(index, values)

    def to_json(self) -> Dict[str, Any]:
        return {"name": self.name, "tables": [t.to_json() for t in self.tables.values()]}

    def save(self, file_path: str | Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Database":
        db = Database(name=data.get("name", "database"))
        for t in data.get("tables", []):
            table = Table.from_json(t)
            db.tables[table.name] = table
        return db

    @classmethod
    def load(cls, file_path: str | Path) -> "Database":
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_json(data)
 

