from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .table import Table


def _row_key(row_values: Dict[str, Any], schema: Tuple[Tuple[str, str], ...]) -> Tuple[str, ...]:
    ordered = []
    for col_name, _ in schema:
        value = row_values.get(col_name)
        ordered.append(json.dumps(value, sort_keys=True, ensure_ascii=False))
    return tuple(ordered)


def union_tables(table1: Table, table2: Table) -> Table:
    if table1.schema_signature() != table2.schema_signature():
        raise ValueError("Schemas do not match for UNION operation")

    result = Table(name=f"{table1.name}_UNION_{table2.name}", columns=table1.columns.copy())
    seen = set()
    schema_sig = table1.schema_signature()

    for row in table1.get_rows() + table2.get_rows():
        key = _row_key(row, schema_sig)
        if key in seen:
            continue
        seen.add(key)
        result.add_row(row)

    return result 

