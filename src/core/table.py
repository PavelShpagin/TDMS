from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple

from .column import Column
from .row import Row
from .validator import TypeValidator


@dataclass
class Table:
    name: str
    columns: List[Column]
    rows: List[Row] = field(default_factory=list)

    @property
    def schema(self) -> List[Tuple[str, str]]:
        return [(c.name, c.type_name) for c in self.columns]

    def add_row(self, values: Dict[str, Any]) -> Row:
        normalized = TypeValidator.validate_row(self.schema, values)
        row = Row(values=normalized)
        self.rows.append(row)
        return row

    def update_row(self, index: int, values: Dict[str, Any]) -> Row:
        if index < 0 or index >= len(self.rows):
            raise IndexError("Row index out of range")
        normalized = TypeValidator.validate_row(self.schema, values)
        self.rows[index] = Row(values=normalized)
        return self.rows[index]

    def get_rows(self) -> List[Dict[str, Any]]:
        # Be resilient if rows were accidentally set as plain dicts
        result: List[Dict[str, Any]] = []
        for r in self.rows:
            if isinstance(r, Row):
                result.append(r.values)
            else:
                # Assume r is already a dict-like mapping
                result.append(dict(r))
        return result

    def schema_signature(self) -> Tuple[Tuple[str, str], ...]:
        return tuple(self.schema)

    def to_json(self) -> Dict[str, Any]:
        # Support both Row instances and plain dicts for robustness
        serialized_rows: List[Dict[str, Any]] = []
        for r in self.rows:
            if isinstance(r, Row):
                serialized_rows.append(r.to_json())
            else:
                serialized_rows.append(dict(r))
        return {
            "name": self.name,
            "columns": [c.to_json() for c in self.columns],
            "rows": serialized_rows,
        }

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Table":
        columns = [Column.from_json(c) for c in data["columns"]]
        table = Table(name=data["name"], columns=columns)
        for r in data.get("rows", []):
            table.rows.append(Row.from_json(r))
        return table

    @staticmethod
    def from_schema(name: str, schema: Iterable[Tuple[str, str]]) -> "Table":
        columns = [Column(n, t) for n, t in schema]
        return Table(name=name, columns=columns)
 

