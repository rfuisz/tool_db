import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tool_db_backend.config import Settings
from tool_db_backend.repository import KnowledgeRepository


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SeedExporter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = KnowledgeRepository(settings)

    def export_bundle(self) -> Dict[str, Any]:
        return {
            "version": "v1",
            "generated_at": _utc_now_iso(),
            "vocabularies": self.repository.get_vocabularies().data,
            "source_registry": self._build_source_registry(),
            "items": self._export_items(),
            "workflows": self._export_workflows(),
        }

    def write_bundle(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.export_bundle(), indent=2) + "\n")
        return output_path

    def write_split_files(self, output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle = self.export_bundle()
        outputs = {
            "controlled_vocabularies.v1.json": bundle["vocabularies"],
            "source_registry.v1.json": bundle["source_registry"],
            "knowledge_seed_bundle.v1.json": {
                "version": bundle["version"],
                "generated_at": bundle["generated_at"],
                "items": bundle["items"],
                "workflows": bundle["workflows"],
            },
        }

        written_paths = []
        for filename, payload in outputs.items():
            path = output_dir / filename
            path.write_text(json.dumps(payload, indent=2) + "\n")
            written_paths.append(path)
        return written_paths

    def _export_items(self) -> List[Dict[str, Any]]:
        items = []
        items_root = self.settings.knowledge_root / "items"
        for item_dir in sorted(path for path in items_root.iterdir() if path.is_dir()):
            items.append(
                {
                    "slug": item_dir.name,
                    "structured": self.repository._read_yaml(item_dir / "structured.yaml"),
                    "index_markdown": self.repository._read_text(item_dir / "index.md"),
                    "evidence_markdown": self.repository._read_text(item_dir / "evidence.md"),
                    "replication_markdown": self.repository._read_text(item_dir / "replication.md"),
                    "workflow_fit_markdown": self.repository._read_text(item_dir / "workflow-fit.md"),
                }
            )
        return items

    def _export_workflows(self) -> List[Dict[str, Any]]:
        workflows = []
        workflow_root = self.settings.knowledge_root / "workflows"
        for workflow_dir in sorted(path for path in workflow_root.iterdir() if path.is_dir()):
            workflows.append(
                {
                    "slug": workflow_dir.name,
                    "structured": self.repository._read_yaml(workflow_dir / "structured.yaml"),
                    "index_markdown": self.repository._read_text(workflow_dir / "index.md"),
                }
            )
        return workflows

    @staticmethod
    def _build_source_registry() -> List[Dict[str, Any]]:
        return [
            {
                "source_key": "optobase",
                "display_name": "OptoBase",
                "source_kind": "database_entry",
                "sync_mode": "seed_then_refresh",
                "role": "curated optogenetics seed catalog",
                "status": "planned",
                "base_url": "https://optobase.org/"
            },
            {
                "source_key": "openalex",
                "display_name": "OpenAlex",
                "source_kind": "database_entry",
                "sync_mode": "periodic_api_sync",
                "role": "work metadata and citation graph",
                "status": "planned",
                "base_url": "https://api.openalex.org/"
            },
            {
                "source_key": "semantic_scholar",
                "display_name": "Semantic Scholar",
                "source_kind": "database_entry",
                "sync_mode": "periodic_api_sync",
                "role": "paper graph and recommendation expansion",
                "status": "planned",
                "base_url": "https://api.semanticscholar.org/"
            },
            {
                "source_key": "clinicaltrials_gov",
                "display_name": "ClinicalTrials.gov",
                "source_kind": "trial_record",
                "sync_mode": "periodic_api_sync",
                "role": "human-use and therapeutic evidence",
                "status": "planned",
                "base_url": "https://clinicaltrials.gov/api/query/"
            },
            {
                "source_key": "gap_map",
                "display_name": "Gap Map",
                "source_kind": "database_entry",
                "sync_mode": "periodic_json_sync",
                "role": "problem catalog for explainable item-gap links",
                "status": "planned",
                "base_url": "https://gap-map.org/"
            }
        ]
