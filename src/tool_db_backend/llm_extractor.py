import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tool_db_backend.config import Settings
from tool_db_backend.schema_validation import validate_packet


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
        if not self.settings.llm_api_key:
            raise LLMExtractionError("LLM API key is not configured.")

        prompt_template_path = self.settings.repo_root / job["prompt_template"]
        schema_path = self.settings.repo_root / job["schema_path"]
        prompt_template = prompt_template_path.read_text()
        schema_text = schema_path.read_text()

        messages = self._build_messages(prompt_template, schema_text, job)
        response = self._client.post(
            "/chat/completions",
            json={
                "model": self.settings.llm_model,
                "messages": messages,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        payload = response.json()
        content = self._extract_content(payload)
        packet = json.loads(content)

        packet_kind = packet.get("packet_type")
        if not packet_kind:
            raise LLMExtractionError("Model response did not include packet_type.")
        validate_packet(packet_kind, packet, self.settings)

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
        return [
            {
                "role": "system",
                "content": (
                    "You are extracting source-backed structured packets for an evidence-first biology database. "
                    "Return only valid JSON that matches the requested schema. "
                    "Never invent canonical IDs or merges."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{prompt_template}\n\n"
                    "## JSON Schema\n"
                    f"{schema_text}\n\n"
                    "## Extraction Job\n"
                    f"{json.dumps(job, indent=2)}\n"
                ),
            },
        ]

    @staticmethod
    def _extract_content(payload: Dict[str, Any]) -> str:
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMExtractionError("Unexpected LLM response shape.") from exc

    def _default_output_path(self, job_path: Optional[Path], packet_kind: str) -> Optional[Path]:
        if job_path is None:
            return None
        return self.settings.extraction_root / f"{job_path.stem}.{packet_kind}.json"
