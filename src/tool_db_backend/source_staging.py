import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.config import Settings
from tool_db_backend.schema_validation import validate_packet


def _clean_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", html.unescape(value or ""))
    return collapsed.strip()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "artifact"


class ClinicalTrialArtifactBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_packet_from_raw_file(self, raw_path: Path, output_path: Path) -> Path:
        raw_wrapper = json.loads(raw_path.read_text())
        payload = raw_wrapper.get("payload", raw_wrapper)
        packet = self.build_packet(payload, raw_payload_ref=str(raw_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(packet, indent=2) + "\n")
        return output_path

    def build_packet(self, payload: Dict[str, Any], raw_payload_ref: Optional[str] = None) -> Dict[str, Any]:
        protocol = payload.get("protocolSection") or {}
        identification = protocol.get("identificationModule") or {}
        status = protocol.get("statusModule") or {}
        description = protocol.get("descriptionModule") or {}
        conditions = protocol.get("conditionsModule") or {}
        design = protocol.get("designModule") or {}
        arms = protocol.get("armsInterventionsModule") or {}

        title = (
            identification.get("briefTitle")
            or identification.get("officialTitle")
            or identification.get("nctId")
            or "ClinicalTrials.gov study"
        )
        packet = {
            "packet_type": "trial_extract_v1",
            "schema_version": "v1",
            "source_document": {
                "source_type": "trial_record",
                "title": title,
                "nct_id": identification.get("nctId"),
                "publication_year": self._extract_year(status),
                "journal_or_source": "ClinicalTrials.gov",
                "abstract_text": description.get("briefSummary") or description.get("detailedDescription"),
                "raw_payload_ref": raw_payload_ref,
            },
            "entity_candidates": [],
            "claims": [],
            "trial_summary": {
                "phase": ", ".join(design.get("phases") or []),
                "recruitment_status": status.get("overallStatus"),
                "condition_or_focus": "; ".join(conditions.get("conditions") or []),
                "intervention_summary": "; ".join(
                    self._format_intervention(intervention)
                    for intervention in (arms.get("interventions") or [])
                    if self._format_intervention(intervention)
                ),
                "study_type": design.get("studyType"),
                "enrollment": self._extract_enrollment(design),
            },
            "validation_observations": [],
            "unresolved_ambiguities": [
                {
                    "issue": "Trial packet is metadata-only staging from ClinicalTrials.gov.",
                    "detail": "Tool, claim, and validation extraction still require curation or a dedicated trial-to-canonical mapping step.",
                    "severity": "medium",
                }
            ],
        }
        validate_packet("trial_extract_v1", packet, self.settings)
        return packet

    @staticmethod
    def _extract_year(status_module: Dict[str, Any]) -> Optional[int]:
        for key in (
            "studyFirstPostDateStruct",
            "startDateStruct",
            "completionDateStruct",
        ):
            date_value = ((status_module.get(key) or {}).get("date") or "").strip()
            if len(date_value) >= 4 and date_value[:4].isdigit():
                return int(date_value[:4])
        return None

    @staticmethod
    def _extract_enrollment(design_module: Dict[str, Any]) -> Optional[int]:
        enrollment = design_module.get("enrollmentInfo") or {}
        count = enrollment.get("count")
        return int(count) if isinstance(count, int) else None

    @staticmethod
    def _format_intervention(intervention: Dict[str, Any]) -> str:
        pieces = [intervention.get("type"), intervention.get("name")]
        return ": ".join(part for part in pieces if part)


class OptoBaseSearchParser:
    RESULT_TITLE_TAGS = ("h2", "h3", "h4")

    def parse_raw_file(self, raw_path: Path) -> Dict[str, Any]:
        raw_wrapper = json.loads(raw_path.read_text())
        return self.parse_html(
            html_text=raw_wrapper.get("payload_text", ""),
            query=str(raw_wrapper.get("external_id") or ""),
            raw_payload_ref=str(raw_path),
        )

    def parse_html(self, html_text: str, query: str = "", raw_payload_ref: Optional[str] = None) -> Dict[str, Any]:
        page_title_match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
        page_title = _clean_text(page_title_match.group(1)) if page_title_match else ""

        titles: List[str] = []
        for tag in self.RESULT_TITLE_TAGS:
            for match in re.finditer(fr"<{tag}[^>]*>(.*?)</{tag}>", html_text, flags=re.IGNORECASE | re.DOTALL):
                text = _clean_text(match.group(1))
                if not text or text == "Curated Optogenetic Publication Database":
                    continue
                if text not in titles:
                    titles.append(text)

        external_links: List[str] = []
        for href in re.findall(r'<a[^>]+href="([^"]+)"', html_text, flags=re.IGNORECASE):
            if href.startswith("https://dx.doi.org/") or href.startswith("https://doi.org/"):
                if href not in external_links:
                    external_links.append(href)

        return {
            "artifact_type": "optobase_search_summary_v1",
            "query": query,
            "page_title": page_title,
            "raw_payload_ref": raw_payload_ref,
            "result_count": len(titles),
            "result_titles": titles[:50],
            "external_fulltext_links": external_links[:50],
        }

    def write_summary_from_raw_file(self, raw_path: Path, output_path: Path) -> Path:
        summary = self.parse_raw_file(raw_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2) + "\n")
        return output_path
