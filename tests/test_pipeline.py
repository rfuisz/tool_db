from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.pipeline import PacketIngestPipeline


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def execute_load_plan(self, load_plan, apply=False, review_output_path=None):
        self.calls.append(
            {
                "load_plan": load_plan,
                "apply": apply,
                "review_output_path": review_output_path,
            }
        )
        return {
            "mode": "applied" if apply else "dry_run",
            "summary": {
                "toolkit_item_actions": len(load_plan["actions"]["toolkit_items"]),
                "claim_actions": len(load_plan["actions"]["claims"]),
                "review_task_count": 0,
                "will_apply_database_changes": apply,
            },
            "review_queue_path": None,
        }


def test_packet_pipeline_writes_artifacts(tmp_path: Path) -> None:
    executor = FakeExecutor()
    pipeline = PacketIngestPipeline(get_settings(), executor=executor)
    packet_path = Path("tests/fixtures/review_extract_v1.sample.json")
    artifact_dir = tmp_path / "artifacts"

    result = pipeline.ingest_packet_file(
        packet_kind="review_extract_v1",
        packet_path=packet_path,
        apply=False,
        artifact_dir=artifact_dir,
    )

    assert result["execution"]["mode"] == "dry_run"
    assert "normalized_packet" in result["artifact_paths"]
    assert Path(result["artifact_paths"]["load_plan"]).exists()
    assert len(executor.calls) == 1


def test_packet_pipeline_passes_apply_flag() -> None:
    executor = FakeExecutor()
    pipeline = PacketIngestPipeline(get_settings(), executor=executor)

    result = pipeline.ingest_packet_file(
        packet_kind="review_extract_v1",
        packet_path=Path("tests/fixtures/review_extract_v1.sample.json"),
        apply=True,
    )

    assert result["execution"]["mode"] == "applied"
    assert executor.calls[0]["apply"] is True


def test_packet_pipeline_skips_metadata_only_primary_paper(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(
        """
{
  "packet_type": "primary_paper_extract_v1",
  "schema_version": "v1",
  "source_document": {
    "source_type": "primary_paper",
    "title": "Metadata only paper"
  },
  "entity_candidates": [],
  "claims": [],
  "validation_observations": [],
  "workflow_stage_observations": [],
  "replication_signals": {},
  "unresolved_ambiguities": []
}
""".strip()
    )
    executor = FakeExecutor()
    settings = get_settings()
    pipeline = PacketIngestPipeline(settings, executor=executor)
    review_output_path = tmp_path / "review-queue.json"

    result = pipeline.ingest_packet_file(
        packet_kind="primary_paper_extract_v1",
        packet_path=packet_path,
        apply=False,
        review_output_path=review_output_path,
    )

    assert result["execution"]["mode"] == "skipped"
    assert result["execution"]["reason"] == "packet_failed_extraction_gate"
    assert len(executor.calls) == 0
    assert review_output_path.exists()
