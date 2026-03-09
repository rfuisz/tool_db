import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tool_db_backend.candidate_filtering import assess_toolkit_item_candidate, load_controlled_vocabularies
from tool_db_backend.config import Settings
from tool_db_backend.entity_resolution import EntityResolver
from tool_db_backend.postgres_loader import LoadPlanExecutionError, PostgresLoadPlanExecutor
from tool_db_backend.schema_validation import PACKET_TO_SCHEMA, PacketValidationError, validate_packet


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unnamed"


def _strip_nul_bytes(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [_strip_nul_bytes(item) for item in value]
    if isinstance(value, dict):
        return {key: _strip_nul_bytes(item) for key, item in value.items()}
    return value


class FirstPassExtractionLoader:
    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection
        self.resolver = EntityResolver(settings)
        self.source_document_writer = PostgresLoadPlanExecutor(settings, connection=connection)
        self._controlled_vocabularies = load_controlled_vocabularies(settings)

    def load_packet_file(self, packet_path: Path) -> Dict[str, Any]:
        payload = _strip_nul_bytes(json.loads(packet_path.read_text()))
        packet_kind = payload.get("packet_type")
        if packet_kind not in PACKET_TO_SCHEMA:
            raise PacketValidationError(f"Unsupported packet kind in {packet_path}: {packet_kind}")
        validate_packet(packet_kind, payload, self.settings)
        packet_fingerprint = hashlib.sha256(packet_path.read_bytes()).hexdigest()

        conn, should_close = self._get_connection()
        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    source_document_id = self.source_document_writer._get_or_create_source_document(  # noqa: SLF001
                        cursor,
                        payload.get("source_document", {}),
                    )
                    extraction_run_id = self._insert_extraction_run(
                        cursor,
                        source_document_id=source_document_id,
                        packet_kind=packet_kind,
                        schema_version=payload.get("schema_version", "v1"),
                        raw_payload_ref=str(packet_path),
                    )
                    self._upsert_packet(
                        cursor,
                        packet_fingerprint=packet_fingerprint,
                        source_document_id=source_document_id,
                        extraction_run_id=extraction_run_id,
                        packet_kind=packet_kind,
                        schema_version=payload.get("schema_version", "v1"),
                        packet_path=str(packet_path),
                        payload=payload,
                    )
                    self._replace_items(
                        cursor,
                        packet_fingerprint=packet_fingerprint,
                        source_document_id=source_document_id,
                        extraction_run_id=extraction_run_id,
                        packet_kind=packet_kind,
                        entity_candidates=payload.get("entity_candidates", []),
                    )
                    claim_count = self._replace_claims(
                        cursor,
                        packet_fingerprint=packet_fingerprint,
                        source_document_id=source_document_id,
                        extraction_run_id=extraction_run_id,
                        packet_kind=packet_kind,
                        claims=payload.get("claims", []),
                    )
        finally:
            if should_close:
                conn.close()

        return {
            "packet_path": str(packet_path),
            "packet_kind": packet_kind,
            "packet_fingerprint": packet_fingerprint,
            "source_document_id": str(source_document_id),
            "extraction_run_id": str(extraction_run_id),
            "entity_candidate_count": len(payload.get("entity_candidates", [])),
            "claim_count": claim_count,
        }

    def load_packet_batch(
        self,
        packet_dir: Path,
        glob_pattern: str = "*.json",
        limit: Optional[int] = None,
        manifest_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        packet_paths = sorted(packet_dir.glob(glob_pattern))
        if limit is not None:
            packet_paths = packet_paths[:limit]
        completed = []
        failures = []
        for packet_path in packet_paths:
            try:
                completed.append(self.load_packet_file(packet_path))
            except (OSError, ValueError, PacketValidationError, LoadPlanExecutionError) as exc:
                failures.append({"packet_path": str(packet_path), "error": str(exc)})
        report = {
            "packet_dir": str(packet_dir),
            "glob_pattern": glob_pattern,
            "selected_packet_count": len(packet_paths),
            "completed_packets": completed,
            "failed_packets": failures,
        }
        if manifest_path:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(report, indent=2) + "\n")
            report["manifest_path"] = str(manifest_path)
        return report

    def _replace_items(
        self,
        cursor: Any,
        *,
        packet_fingerprint: str,
        source_document_id: Any,
        extraction_run_id: Any,
        packet_kind: str,
        entity_candidates: List[Dict[str, Any]],
    ) -> None:
        cursor.execute("delete from extracted_item_candidate where packet_fingerprint = %s", (packet_fingerprint,))
        filtered_entities = self._filter_item_candidates(entity_candidates)
        resolved_items = self._resolve_item_candidates(filtered_entities)
        for entity in filtered_entities:
            canonical_name = str(entity.get("canonical_name", "")).strip()
            slug = _slugify(canonical_name)
            matched_slug, matched_item_id = resolved_items.get(entity.get("local_id"), (None, None))
            cursor.execute(
                """
                insert into extracted_item_candidate (
                  packet_fingerprint, source_document_id, extraction_run_id, packet_kind,
                  local_id, candidate_type, slug, canonical_name, item_type, aliases,
                  external_ids, evidence_text, matched_item_id, matched_slug, raw_payload
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::text[], %s::jsonb, %s, %s, %s, %s::jsonb)
                """,
                (
                    packet_fingerprint,
                    source_document_id,
                    extraction_run_id,
                    packet_kind,
                    entity.get("local_id"),
                    entity.get("candidate_type"),
                    slug,
                    canonical_name,
                    entity.get("item_type"),
                    entity.get("aliases", []),
                    json.dumps(entity.get("external_ids", {})),
                    entity.get("evidence_text"),
                    matched_item_id,
                    matched_slug,
                    json.dumps(entity),
                ),
            )

    def _filter_item_candidates(self, entity_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        allowed_item_types = set(self._controlled_vocabularies.get("item_types", []))
        filtered = []
        for entity in entity_candidates:
            if entity.get("candidate_type") != "toolkit_item":
                filtered.append(entity)
                continue
            assessment = assess_toolkit_item_candidate(entity, allowed_item_types=allowed_item_types)
            if not assessment["keep"]:
                continue
            normalized_entity = dict(entity)
            normalized_entity["item_type"] = assessment["item_type"]
            filtered.append(normalized_entity)
        return filtered

    def _replace_claims(
        self,
        cursor: Any,
        *,
        packet_fingerprint: str,
        source_document_id: Any,
        extraction_run_id: Any,
        packet_kind: str,
        claims: List[Dict[str, Any]],
    ) -> int:
        cursor.execute("delete from extracted_claim_candidate where packet_fingerprint = %s", (packet_fingerprint,))
        item_ids_by_local_id = self._load_item_candidate_ids(cursor, packet_fingerprint)
        inserted_count = 0
        for claim in claims:
            cursor.execute(
                """
                insert into extracted_claim_candidate (
                  packet_fingerprint, source_document_id, extraction_run_id, packet_kind,
                  local_id, claim_type, claim_text_normalized, polarity, context, metrics,
                  source_locator, unresolved_ambiguities, raw_payload
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
                returning id
                """,
                (
                    packet_fingerprint,
                    source_document_id,
                    extraction_run_id,
                    packet_kind,
                    claim.get("local_id"),
                    claim.get("claim_type"),
                    claim.get("claim_text_normalized"),
                    claim.get("polarity"),
                    json.dumps(claim.get("context", {})),
                    json.dumps(claim.get("metrics", [])),
                    json.dumps(claim.get("source_locator", {})),
                    json.dumps(claim.get("unresolved_ambiguities", [])),
                    json.dumps(claim),
                ),
            )
            claim_id = cursor.fetchone()[0]
            inserted_count += 1
            for subject_local_id in claim.get("subject_local_ids", []):
                item_id = item_ids_by_local_id.get(subject_local_id)
                if not item_id:
                    continue
                cursor.execute(
                    """
                    insert into extracted_claim_subject_candidate (
                      extracted_claim_candidate_id, extracted_item_candidate_id, subject_role
                    )
                    values (%s, %s, %s)
                    on conflict do nothing
                    """,
                    (claim_id, item_id, "subject"),
                )
        return inserted_count

    @staticmethod
    def _load_item_candidate_ids(cursor: Any, packet_fingerprint: str) -> Dict[str, Any]:
        cursor.execute(
            """
            select local_id, id
            from extracted_item_candidate
            where packet_fingerprint = %s
            """,
            (packet_fingerprint,),
        )
        return {row[0]: row[1] for row in cursor.fetchall()}

    def _resolve_item_candidates(self, entity_candidates: List[Dict[str, Any]]) -> Dict[str, Tuple[Optional[str], Optional[Any]]]:
        candidate_payload = {}
        for entity in entity_candidates:
            if entity.get("candidate_type") != "toolkit_item":
                continue
            canonical_name = str(entity.get("canonical_name", "")).strip()
            candidate_payload[entity["local_id"]] = {
                "slug": _slugify(canonical_name),
                "canonical_name": canonical_name,
                "item_type": entity.get("item_type"),
                "aliases": entity.get("aliases", []),
                "external_ids": entity.get("external_ids", {}),
            }
        resolutions = self.resolver.resolve_item_candidates(candidate_payload)
        matched = {}
        conn, should_close = self._get_connection()
        try:
            with conn.cursor() as cursor:
                for local_id, resolution in resolutions.items():
                    if resolution.get("resolution_status") != "matched_existing":
                        matched[local_id] = (None, None)
                        continue
                    matched_slug = resolution["matched_slug"]
                    cursor.execute("select id from toolkit_item where slug = %s", (matched_slug,))
                    row = cursor.fetchone()
                    matched[local_id] = (matched_slug, row[0] if row else None)
        finally:
            if should_close:
                conn.close()
        for entity in entity_candidates:
            matched.setdefault(entity.get("local_id"), (None, None))
        return matched

    @staticmethod
    def _upsert_packet(
        cursor: Any,
        *,
        packet_fingerprint: str,
        source_document_id: Any,
        extraction_run_id: Any,
        packet_kind: str,
        schema_version: str,
        packet_path: str,
        payload: Dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            insert into extracted_packet (
              packet_fingerprint, source_document_id, extraction_run_id, packet_kind,
              schema_version, packet_path, packet_payload
            )
            values (%s, %s, %s, %s, %s, %s, %s::jsonb)
            on conflict (packet_fingerprint) do update
            set
              source_document_id = excluded.source_document_id,
              extraction_run_id = excluded.extraction_run_id,
              packet_kind = excluded.packet_kind,
              schema_version = excluded.schema_version,
              packet_path = excluded.packet_path,
              packet_payload = excluded.packet_payload
            """,
            (
                packet_fingerprint,
                source_document_id,
                extraction_run_id,
                packet_kind,
                schema_version,
                packet_path,
                json.dumps(payload),
            ),
        )

    @staticmethod
    def _insert_extraction_run(
        cursor: Any,
        *,
        source_document_id: Any,
        packet_kind: str,
        schema_version: str,
        raw_payload_ref: str,
    ) -> Any:
        cursor.execute(
            """
            insert into extraction_run (
              source_document_id, packet_kind, schema_version, status, raw_payload_ref
            )
            values (%s, %s, %s, %s, %s)
            returning id
            """,
            (source_document_id, packet_kind, schema_version, "completed", raw_payload_ref),
        )
        return cursor.fetchone()[0]

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to load first-pass extraction data.")
        import psycopg

        return psycopg.connect(self.settings.database_url), True
