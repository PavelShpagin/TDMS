from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    type_name: str

    def to_json(self) -> dict:
        return {"name": self.name, "type": self.type_name}

    @staticmethod
    def from_json(data: dict) -> "Column":
        return Column(name=data["name"], type_name=data["type"]) 

