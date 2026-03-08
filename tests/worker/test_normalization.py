import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.normalization import PacketNormalizer


def test_review_packet_normalization_maps_candidates_and_claims() -> None:
    fixture_path = Path("tests/fixtures/review_extract_v1.sample.json")
    payload = json.loads(fixture_path.read_text())
    normalizer = PacketNormalizer(get_settings())

    normalized = normalizer.normalize_packet("review_extract_v1", payload)

    assert normalized["normalized_packet_type"] == "review_extract_normalized_v1"
    assert normalized["canonical_item_candidates"]["item_aslov2"]["candidate_key"] == "item/aslov2"
    assert normalized["canonical_item_candidates"]["item_cry2_cib1"]["candidate_key"] == "item/cry2-cib1"
    assert (
        normalized["canonical_workflow_candidates"]["workflow_fast_no_cloning_screen"]["candidate_key"]
        == "workflow/fast-no-cloning-screen"
    )
    assert normalized["claims"][0]["subject_candidate_keys"] == ["item/aslov2"]
    assert (
        normalized["workflow_stage_observations"][0]["workflow_candidate_key"]
        == "workflow/fast-no-cloning-screen"
    )
    assert normalized["recommended_seed_item_keys"] == ["item/aslov2", "item/cry2-cib1"]


def test_normalizer_writes_output_file(tmp_path: Path) -> None:
    fixture_path = Path("tests/fixtures/review_extract_v1.sample.json")
    output_path = tmp_path / "normalized.json"
    normalizer = PacketNormalizer(get_settings())

    written_path = normalizer.write_normalized_packet(
        "review_extract_v1",
        fixture_path,
        output_path,
    )

    assert written_path == output_path
    payload = json.loads(output_path.read_text())
    assert payload["normalized_packet_type"] == "review_extract_normalized_v1"
