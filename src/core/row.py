from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Row:
    values: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        return self.values

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Row":
        return Row(values=dict(data)) 

