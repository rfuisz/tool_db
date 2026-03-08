import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tool_db_backend.config import Settings
from tool_db_backend.llm_json_client import LLMJSONCallError, run_cached_json_chat_completion
from tool_db_backend.schema_validation import PacketValidationError, validate_packet


class LLMExtractionError(RuntimeError):
    pass


class LLMExtractionRunner:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        self._client = client or self._build_client()

    def close(self) -> None:
        self._client.close()

    def run_job_file(self, job_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        job = json.loads(job_path.read_text())
        return self.run_job(job, output_path=output_path, job_path=job_path)

    def run_job(
        self,
        job: Dict[str, Any],
        output_path: Optional[Path] = None,
        job_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        prompt_template_path = self.settings.repo_root / job["prompt_template"]
        schema_path = self.settings.repo_root / job["schema_path"]
        prompt_template = prompt_template_path.read_text()
        schema_text = schema_path.read_text()

        messages = self._build_messages(prompt_template, schema_text, job)
        packet = self._request_json_object(
            purpose=f"extraction:{job.get('target_packet_type', 'unknown')}",
            messages=messages,
        )

        packet = self._validate_with_repairs(job, prompt_template, schema_text, packet)
        packet_kind = packet["packet_type"]

        final_output_path = output_path or self._default_output_path(job_path, packet_kind)
        if final_output_path is not None:
            final_output_path.parent.mkdir(parents=True, exist_ok=True)
            final_output_path.write_text(json.dumps(packet, indent=2) + "\n")

        return {
            "job_path": str(job_path) if job_path else None,
            "output_path": str(final_output_path) if final_output_path else None,
            "packet_type": packet_kind,
            "model": self.settings.llm_model,
        }

    def _build_client(self) -> httpx.Client:
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        return httpx.Client(
            base_url=self.settings.llm_base_url,
            headers=headers,
            timeout=120.0,
        )

    def _build_messages(
        self,
        prompt_template: str,
        schema_text: str,
        job: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        common_schema_path = self.settings.repo_root / "schemas" / "extraction" / "common.v1.schema.json"
        common_schema_text = common_schema_path.read_text()
        return [
            {
                "role": "system",
                "content": (
                    "You are extracting source-backed structured packets for an evidence-first biology database. "
                    "Return only valid JSON that matches the requested schema. "
                    "Never invent canonical IDs or merges. "
                    "Do not return extra properties that are not in the schema."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{prompt_template}\n\n"
                    "## JSON Schema\n"
                    f"{schema_text}\n\n"
                    "## Common JSON Schema Definitions\n"
                    f"{common_schema_text}\n\n"
                    "## Extraction Job\n"
                    f"{json.dumps(job, indent=2)}\n"
                ),
            },
        ]

    def _repair_packet(
        self,
        job: Dict[str, Any],
        prompt_template: str,
        schema_text: str,
        invalid_packet: Dict[str, Any],
        validation_error: str,
    ) -> Dict[str, Any]:
        common_schema_path = self.settings.repo_root / "schemas" / "extraction" / "common.v1.schema.json"
        common_schema_text = common_schema_path.read_text()
        return self._request_json_object(
            purpose=f"repair:{job.get('target_packet_type', 'unknown')}",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are repairing an invalid JSON extraction packet. "
                        "Return only corrected JSON that exactly matches the schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{prompt_template}\n\n"
                        "## JSON Schema\n"
                        f"{schema_text}\n\n"
                        "## Common JSON Schema Definitions\n"
                        f"{common_schema_text}\n\n"
                        "## Original Extraction Job\n"
                        f"{json.dumps(job, indent=2)}\n\n"
                        "## Invalid Packet\n"
                        f"{json.dumps(invalid_packet, indent=2)}\n\n"
                        "## Validation Error\n"
                        f"{validation_error}\n"
                    ),
                },
            ],
        )

    def _validate_with_repairs(
        self,
        job: Dict[str, Any],
        prompt_template: str,
        schema_text: str,
        packet: Dict[str, Any],
    ) -> Dict[str, Any]:
        last_error = None
        current_packet = packet
        for _ in range(4):
            packet_kind = current_packet.get("packet_type")
            if not packet_kind:
                last_error = "Model response did not include packet_type."
            else:
                try:
                    validate_packet(packet_kind, current_packet, self.settings)
                    return current_packet
                except PacketValidationError as exc:
                    last_error = str(exc)
            current_packet = self._repair_packet(
                job,
                prompt_template,
                schema_text,
                current_packet,
                last_error or "Unknown validation error.",
            )
        raise LLMExtractionError(f"LLM extraction could not be repaired to schema-valid JSON: {last_error}")

    def _default_output_path(self, job_path: Optional[Path], packet_kind: str) -> Optional[Path]:
        if job_path is None:
            return None
        return self.settings.extraction_root / f"{job_path.stem}.{packet_kind}.json"

    def _request_json_object(self, *, purpose: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            return run_cached_json_chat_completion(
                self.settings,
                self._client,
                purpose=purpose,
                messages=messages,
            )
        except LLMJSONCallError as exc:
            raise LLMExtractionError(str(exc)) from exc
