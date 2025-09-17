from __future__ import annotations

import json
from typing import Any, Dict, Tuple, List

from .table import Table
from .column import Column
from .row import Row


def _row_key(row_values: Dict[str, Any], schema: Tuple[Tuple[str, str], ...]) -> Tuple[str, ...]:
	ordered = []
	for col_name, _ in schema:
		value = row_values.get(col_name)
		ordered.append(json.dumps(value, sort_keys=True, ensure_ascii=False))
	return tuple(ordered)


def union_tables(table1: Table, table2: Table) -> Table:
	# Compatibility: overlapping columns must have the same type
	left = {n: t for n, t in table1.schema}
	right = {n: t for n, t in table2.schema}
	for name in set(left.keys()) & set(right.keys()):
		if left[name] != right[name]:
			raise ValueError(f"Incompatible schemas: column '{name}' types differ ({left[name]} vs {right[name]})")

	# Build combined schema: preserve table1 order, then append new columns from table2
	name_to_type: Dict[str, str] = {n: t for n, t in table1.schema}
	combined: List[Tuple[str, str]] = list(table1.schema)
	for n, t in table2.schema:
		if n not in name_to_type:
			name_to_type[n] = t
			combined.append((n, t))

	result = Table.from_schema(name=f"{table1.name}_UNION_{table2.name}", schema=combined)

	# UNION ALL semantics: append all rows from both tables; fill missing with None
	schema_sig = result.schema_signature()

	def append_row(raw: Dict[str, Any]) -> None:
		full = {col: raw.get(col, None) for col, _ in schema_sig}
		result.rows.append(Row(values=full))

	for row in table1.get_rows():
		append_row(row)
	for row in table2.get_rows():
		append_row(row)

	return result 

