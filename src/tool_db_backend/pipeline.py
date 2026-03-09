import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from tool_db_backend.config import Settings
from tool_db_backend.extraction_gate import ExtractionGate
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer
from tool_db_backend.postgres_loader import PostgresLoadPlanExecutor
from tool_db_backend.review_queue import ReviewQueueWriter
from tool_db_backend.schema_validation import validate_packet


class PacketIngestPipeline:
    def __init__(self, settings: Settings, executor: Optional[PostgresLoadPlanExecutor] = None) -> None:
        self.settings = settings
        self.extraction_gate = ExtractionGate()
        self.normalizer = PacketNormalizer(settings)
        self.load_plan_builder = LoadPlanBuilder(settings)
        self.executor = executor or PostgresLoadPlanExecutor(settings)
        self.review_writer = ReviewQueueWriter(settings)

    def ingest_packet_file(
        self,
        packet_kind: str,
        packet_path: Path,
        apply: bool = False,
        artifact_dir: Optional[Path] = None,
        review_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        payload = json.loads(packet_path.read_text())
        validate_packet(packet_kind, payload, self.settings)
        gate_result = self.extraction_gate.assess(packet_kind, payload)
        if not gate_result["is_ready"]:
            review_queue_path = self.review_writer.write_tasks(
                source_document=payload.get("source_document", {}),
                tasks=[
                    {
                        "task_type": "extraction_packet_review",
                        "packet_kind": packet_kind,
                        "reason": issue,
                    }
                    for issue in gate_result["issues"]
                ],
                output_path=review_output_path,
            )
            execution = {
                "mode": "skipped",
                "reason": "packet_failed_extraction_gate",
                "issues": gate_result["issues"],
                "review_queue_path": str(review_queue_path),
            }
            artifact_paths = {}
            if artifact_dir is not None:
                artifact_paths = self._write_artifacts(
                    artifact_dir=artifact_dir,
                    packet_path=packet_path,
                    packet_kind=packet_kind,
                    normalized={},
                    load_plan={},
                    execution=execution,
                )
            return {
                "packet_kind": packet_kind,
                "packet_path": str(packet_path),
                "execution": execution,
                "artifact_paths": artifact_paths,
            }

        normalized = self.normalizer.normalize_packet(packet_kind, payload)
        load_plan = self.load_plan_builder.build_from_normalized_payload(normalized)
        execution = self.executor.execute_load_plan(
            load_plan,
            apply=apply,
            review_output_path=review_output_path,
        )

        artifact_paths = {}
        if artifact_dir is not None:
            artifact_paths = self._write_artifacts(
                artifact_dir=artifact_dir,
                packet_path=packet_path,
                packet_kind=packet_kind,
                normalized=normalized,
                load_plan=load_plan,
                execution=execution,
            )

        return {
            "packet_kind": packet_kind,
            "packet_path": str(packet_path),
            "execution": execution,
            "artifact_paths": artifact_paths,
        }

    def _write_artifacts(
        self,
        artifact_dir: Path,
        packet_path: Path,
        packet_kind: str,
        normalized: Dict[str, Any],
        load_plan: Dict[str, Any],
        execution: Dict[str, Any],
    ) -> Dict[str, str]:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        stem = build_artifact_basename(packet_path)
        paths = {
            "normalized_packet": artifact_dir / f"{stem}.{packet_kind}.normalized.json",
            "load_plan": artifact_dir / f"{stem}.{packet_kind}.load-plan.json",
            "execution_report": artifact_dir / f"{stem}.{packet_kind}.execution.json",
        }
        paths["normalized_packet"].write_text(json.dumps(normalized, indent=2) + "\n")
        paths["load_plan"].write_text(json.dumps(load_plan, indent=2) + "\n")
        paths["execution_report"].write_text(json.dumps(execution, indent=2) + "\n")
        return {key: str(path) for key, path in paths.items()}


def build_artifact_basename(packet_path: Path, max_length: int = 80) -> str:
    stem = packet_path.stem
    if len(stem) <= max_length:
        return stem
    digest = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:12]
    prefix_budget = max_length - len(digest) - 1
    prefix = stem[: max(prefix_budget, 8)].rstrip("-_.")
    return f"{prefix}-{digest}"
