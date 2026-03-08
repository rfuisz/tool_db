import json
from pathlib import Path
from typing import Any, Dict, Optional

from tool_db_backend.config import Settings
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer
from tool_db_backend.postgres_loader import PostgresLoadPlanExecutor
from tool_db_backend.schema_validation import validate_packet


class PacketIngestPipeline:
    def __init__(self, settings: Settings, executor: Optional[PostgresLoadPlanExecutor] = None) -> None:
        self.settings = settings
        self.normalizer = PacketNormalizer(settings)
        self.load_plan_builder = LoadPlanBuilder(settings)
        self.executor = executor or PostgresLoadPlanExecutor(settings)

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
        stem = packet_path.stem
        paths = {
            "normalized_packet": artifact_dir / f"{stem}.{packet_kind}.normalized.json",
            "load_plan": artifact_dir / f"{stem}.{packet_kind}.load-plan.json",
            "execution_report": artifact_dir / f"{stem}.{packet_kind}.execution.json",
        }
        paths["normalized_packet"].write_text(json.dumps(normalized, indent=2) + "\n")
        paths["load_plan"].write_text(json.dumps(load_plan, indent=2) + "\n")
        paths["execution_report"].write_text(json.dumps(execution, indent=2) + "\n")
        return {key: str(path) for key, path in paths.items()}
