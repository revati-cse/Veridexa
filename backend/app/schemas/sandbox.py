import re

from pydantic import BaseModel, field_validator

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str) -> str:
    if not _IDENTIFIER_PATTERN.match(value):
        raise ValueError(f"'{value}' is not a valid SQL identifier")
    return value


class SandboxTable(BaseModel):
    """One table to seed into the in-memory SQLite sandbox before running a
    candidate's query. `rows` is a list of value-lists, one per `columns`."""

    name: str
    columns: list[str]
    rows: list[list] = []

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return _validate_identifier(value)

    @field_validator("columns")
    @classmethod
    def _validate_columns(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("A table must declare at least one column")
        return [_validate_identifier(c) for c in value]


class SandboxDataset(BaseModel):
    """The seed data behind a Challenge's `dataset` field, once the sandbox
    parses it. Identifiers are restricted to safe characters (checked above)
    since this content may ultimately come from an LLM-generated challenge —
    it is untrusted input, not just internal config."""

    tables: list[SandboxTable]
