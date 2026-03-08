import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.seed_export import SeedExporter


def test_seed_export_bundle_contains_expected_sections() -> None:
    exporter = SeedExporter(get_settings())

    bundle = exporter.export_bundle()

    assert bundle["version"] == "v1"
    assert "vocabularies" in bundle
    assert "items" in bundle
    assert "workflows" in bundle
    assert "source_registry" in bundle
    assert any(item["slug"] == "aslov2" for item in bundle["items"])
    assert any(workflow["slug"] == "fast-no-cloning-screen" for workflow in bundle["workflows"])


def test_seed_export_writes_split_files(tmp_path: Path) -> None:
    exporter = SeedExporter(get_settings())

    written_paths = exporter.write_split_files(tmp_path)

    expected_names = {
        "controlled_vocabularies.v1.json",
        "source_registry.v1.json",
        "knowledge_seed_bundle.v1.json",
    }
    assert {path.name for path in written_paths} == expected_names
    for path in written_paths:
        assert json.loads(path.read_text())
