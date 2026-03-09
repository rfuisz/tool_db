import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer


def test_load_plan_builder_creates_existing_item_actions() -> None:
    payload = json.loads(Path("tests/fixtures/review_extract_v1.sample.json").read_text())
    normalizer = PacketNormalizer(get_settings())
    normalized = normalizer.normalize_packet("review_extract_v1", payload)
    builder = LoadPlanBuilder(get_settings())

    load_plan = builder.build_from_normalized_payload(normalized)

    assert load_plan["load_plan_type"] == "canonical_load_plan_v1"
    toolkit_actions = load_plan["actions"]["toolkit_items"]
    assert any(action["action"] == "attach_evidence_to_existing_item" for action in toolkit_actions)
    attach_action = next(
        action for action in toolkit_actions if action["action"] == "attach_evidence_to_existing_item"
    )
    assert attach_action["summary"]
    claim_actions = load_plan["actions"]["claims"]
    assert claim_actions[0]["subject_targets"][0]["target_kind"] == "existing_item"
    workflow_actions = load_plan["actions"]["workflows"]
    assert workflow_actions[0]["action"] == "upsert_workflow_for_existing_workflow"
    assert workflow_actions[0]["target_slug"] == "fast-no-cloning-screen"
    assert len(workflow_actions[0]["stages"]) == 2


def test_load_plan_builder_summary_prefers_extracted_explainer_text() -> None:
    builder = LoadPlanBuilder(get_settings())

    summary = builder._derive_summary(  # noqa: SLF001
        {
            "freeform_explainers": {
                "what_it_does": "Provides light-gated recruitment in the source-backed extraction output."
            },
            "useful_for": ["control transcription timing"],
            "problem_solved": ["reduce constitutive recruitment"],
        },
        [],
    )

    assert summary == "Provides light-gated recruitment in the source-backed extraction output."


def test_load_plan_builder_summary_skips_name_only_evidence_text() -> None:
    builder = LoadPlanBuilder(get_settings())

    summary = builder._derive_summary(  # noqa: SLF001
        {
            "canonical_name": "Am1_c0023g2",
            "evidence_text": "the CBCR Am1_c0023g2",
        },
        [
            {
                "claim_type": "engineering_result",
                "claim_text_normalized": (
                    "AM1_C0023g2 covalently binds both phycocyanobilin and biliverdin with high binding efficiencies."
                ),
            }
        ],
    )

    assert summary == "AM1_C0023g2 covalently binds both phycocyanobilin and biliverdin with high binding efficiencies."


def test_load_plan_writer_outputs_json(tmp_path: Path) -> None:
    payload = json.loads(Path("tests/fixtures/review_extract_v1.sample.json").read_text())
    normalizer = PacketNormalizer(get_settings())
    normalized_path = tmp_path / "normalized.json"
    normalizer.write_normalized_packet("review_extract_v1", Path("tests/fixtures/review_extract_v1.sample.json"), normalized_path)

    builder = LoadPlanBuilder(get_settings())
    output_path = tmp_path / "load-plan.json"
    builder.write_load_plan(normalized_path, output_path)

    written = json.loads(output_path.read_text())
    assert written["load_plan_type"] == "canonical_load_plan_v1"
