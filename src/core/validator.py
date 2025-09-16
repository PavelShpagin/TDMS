from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, Tuple


class TypeValidator:
    SUPPORTED_TYPES = {"integer", "real", "char", "string", "date", "dateInvl"}

    @staticmethod
    def _ensure_supported(type_name: str) -> None:
        if type_name not in TypeValidator.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported type: {type_name}")

    @staticmethod
    def _parse_date(value: Any) -> str:
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            try:
                return date.fromisoformat(value).isoformat()
            except ValueError as exc:
                raise ValueError("Invalid date format, expected YYYY-MM-DD") from exc
        raise ValueError("Invalid date value")

    @staticmethod
    def normalize(value: Any, type_name: str) -> Any:
        TypeValidator._ensure_supported(type_name)

        if type_name == "integer":
            if isinstance(value, bool):
                raise ValueError("Boolean is not accepted as integer")
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid integer") from exc

        if type_name == "real":
            if isinstance(value, bool):
                raise ValueError("Boolean is not accepted as real")
            try:
                return float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid real") from exc

        if type_name == "char":
            if not isinstance(value, str):
                raise ValueError("Invalid char")
            if len(value) != 1:
                raise ValueError("Char must be exactly one character")
            return value

        if type_name == "string":
            if isinstance(value, (str, bytes)):
                return value.decode() if isinstance(value, bytes) else value
            return str(value)

        if type_name == "date":
            return TypeValidator._parse_date(value)

        if type_name == "dateInvl":
            # Accept dict with start/end, tuple/list of two, or "start..end" string
            start: Any
            end: Any
            if isinstance(value, dict) and "start" in value and "end" in value:
                start = value["start"]
                end = value["end"]
            elif isinstance(value, (tuple, list)) and len(value) == 2:
                start, end = value
            elif isinstance(value, str) and ".." in value:
                start, end = value.split("..", 1)
            else:
                raise ValueError("Invalid dateInvl, expected {start,end}, [start,end] or 'start..end'")

            start_iso = TypeValidator._parse_date(start)
            end_iso = TypeValidator._parse_date(end)
            if start_iso > end_iso:
                raise ValueError("dateInvl start must be <= end")
            return {"start": start_iso, "end": end_iso}

        raise ValueError(f"Unknown type: {type_name}")

    @staticmethod
    def validate_row(schema: Iterable[Tuple[str, str]], values: Dict[str, Any]) -> Dict[str, Any]:
        schema_list = list(schema)
        normalized: Dict[str, Any] = {}

        # Ensure no extra keys
        allowed_keys = {name for name, _ in schema_list}
        extra = set(values.keys()) - allowed_keys
        if extra:
            raise ValueError(f"Unexpected columns: {sorted(extra)}")

        for name, type_name in schema_list:
            if name not in values:
                raise ValueError(f"Missing value for column '{name}'")
            normalized[name] = TypeValidator.normalize(values[name], type_name)

        return normalized 

