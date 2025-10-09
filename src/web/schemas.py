from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


# ---- Typenames and boilerplate shared types ----

class ColumnSchema(BaseModel):
    name: str
    type: str = Field(alias="type")


class CreateTableRequest(BaseModel):
    name: str
    # Avoid shadowing BaseModel.schema; accept incoming key "schema" as alias
    columns: List[ColumnSchema] = Field(alias="schema")
    model_config = ConfigDict(populate_by_name=True)


class InsertRowRequest(BaseModel):
    values: Dict[str, object]


class UpdateRowRequest(BaseModel):
    values: Dict[str, object]


class CreateDatabaseRequest(BaseModel):
    name: str


class RenameDatabaseRequest(BaseModel):
    old: Optional[str] = None
    new: str


class SwitchOrDeleteDatabaseRequest(BaseModel):
    name: str


class SaveRequest(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None


class LoadRequest(BaseModel):
    name: str
    path: Optional[str] = None


class ExportQuery(BaseModel):
    name: Optional[str] = None


class ImportDatabaseRequest(BaseModel):
    name: str
    data: Dict[str, object] | str


class UnionRequest(BaseModel):
    left: str
    right: str
    name: Optional[str] = None


class GoogleTokenSaveRequest(BaseModel):
    refresh_token: Optional[str] = None
    code: Optional[str] = None


class GoogleAccessTokenRequest(BaseModel):
    access_token: str
    expires_in: Optional[int] = None


