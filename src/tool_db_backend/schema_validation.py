import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

from tool_db_backend.config import Settings


PACKET_TO_SCHEMA = {
    "review_extract_v1": "review_extract.v1.schema.json",
    "primary_paper_extract_v1": "primary_paper_extract.v1.schema.json",
    "trial_extract_v1": "trial_extract.v1.schema.json",
    "database_entry_extract_v1": "database_entry_extract.v1.schema.json",
}


class PacketValidationError(ValueError):
    pass


@lru_cache(maxsize=1)
def _build_registry(schema_root: Path) -> Registry:
    registry = Registry()
    for path in schema_root.glob("extraction/*.json"):
        contents = json.loads(path.read_text())
        schema_id = contents.get("$id")
        if schema_id:
            registry = registry.with_resource(schema_id, Resource.from_contents(contents))
    return registry


@lru_cache(maxsize=8)
def _load_schema(settings_repo_root: Path, schema_name: str) -> Dict[str, Any]:
    schema_path = settings_repo_root / "schemas" / "extraction" / schema_name
    return json.loads(schema_path.read_text())


def validate_packet(packet_kind: str, payload: Dict[str, Any], settings: Settings) -> None:
    schema_name = PACKET_TO_SCHEMA.get(packet_kind)
    if schema_name is None:
        raise PacketValidationError(f"Unsupported packet kind: {packet_kind}")

    registry = _build_registry(settings.schema_root)
    schema = _load_schema(settings.repo_root, schema_name)
    validator = Draft202012Validator(schema, registry=registry)
    try:
        validator.validate(payload)
    except ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = path or "<root>"
        raise PacketValidationError(f"{location}: {exc.message}") from exc
