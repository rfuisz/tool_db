from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx
from jsonschema import Draft202012Validator, ValidationError

from tool_db_backend.config import Settings
from tool_db_backend.item_materialization import ItemMaterializer
from tool_db_backend.llm_json_client import LLMJSONCallError, run_cached_json_chat_completion

GAP_LINK_SCORE_VERSION = "gpt_gap_link_v1"
DEFAULT_EXCLUDED_ITEM_TYPES = {"protein_domain"}
DEFAULT_MAX_CANDIDATES_PER_GAP = 12
DEFAULT_MAX_LINKS_PER_GAP = 6
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "with",
}


class GapLinkingError(RuntimeError):
    pass


def _normalize_text(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().split())


def _tokenize(values: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for token in _TOKEN_RE.findall(value.casefold()):
            if len(token) < 3 or token in _STOPWORDS:
                continue
            tokens.add(token)
    return tokens


def _clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, round(numeric, 3)))


@dataclass
class ItemProfile:
    item_id: Any
    slug: str
    canonical_name: str
    item_type: str
    summary: Optional[str]
    primary_input_modality: Optional[str]
    primary_output_modality: Optional[str]
    mechanisms: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    target_processes: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    facet_hints: List[str] = field(default_factory=list)
    replication_summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def text_blob(self) -> str:
        return " ".join(
            part
            for part in [
                self.canonical_name,
                self.summary or "",
                " ".join(self.synonyms),
                " ".join(self.mechanisms),
                " ".join(self.techniques),
                " ".join(self.target_processes),
                " ".join(self.facet_hints),
                self.primary_input_modality or "",
                self.primary_output_modality or "",
            ]
            if part
        ).casefold()

    @property
    def keyword_tokens(self) -> set[str]:
        return _tokenize(
            [
                self.canonical_name,
                self.summary or "",
                *self.synonyms,
                *self.mechanisms,
                *self.techniques,
                *self.target_processes,
                *self.facet_hints,
            ]
        )

    def llm_payload(self) -> Dict[str, Any]:
        return {
            "item_slug": self.slug,
            "canonical_name": self.canonical_name,
            "item_type": self.item_type,
            "summary": self.summary,
            "primary_input_modality": self.primary_input_modality,
            "primary_output_modality": self.primary_output_modality,
            "mechanisms": self.mechanisms,
            "techniques": self.techniques,
            "target_processes": self.target_processes,
            "facet_hints": self.facet_hints,
            "replication_summary": {
                "replication_score": self.replication_summary.get("replication_score"),
                "practicality_score": self.replication_summary.get("practicality_score"),
                "translatability_score": self.replication_summary.get("translatability_score"),
                "primary_paper_count": self.replication_summary.get("primary_paper_count"),
                "independent_primary_paper_count": self.replication_summary.get(
                    "independent_primary_paper_count"
                ),
            },
        }


@dataclass
class GapProfile:
    gap_item_id: Any
    slug: str
    title: str
    field_name: Optional[str]
    description: Optional[str]
    tags: List[str] = field(default_factory=list)
    capabilities: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def text_blob(self) -> str:
        capability_bits: List[str] = []
        for capability in self.capabilities:
            capability_bits.append(capability.get("name") or "")
            capability_bits.append(capability.get("description") or "")
            capability_bits.extend(capability.get("tags") or [])
            capability_bits.extend(capability.get("resources") or [])
        return " ".join(
            part
            for part in [
                self.title,
                self.field_name or "",
                self.description or "",
                " ".join(self.tags),
                " ".join(capability_bits),
            ]
            if part
        ).casefold()

    @property
    def keyword_tokens(self) -> set[str]:
        values = [self.title, self.field_name or "", self.description or "", *self.tags]
        for capability in self.capabilities:
            values.append(capability.get("name") or "")
            values.append(capability.get("description") or "")
            values.extend(capability.get("tags") or [])
            values.extend(capability.get("resources") or [])
        return _tokenize(values)

    def llm_payload(self) -> Dict[str, Any]:
        return {
            "gap_slug": self.slug,
            "title": self.title,
            "field_name": self.field_name,
            "description": self.description,
            "tags": self.tags,
            "capabilities": self.capabilities,
        }


class GapLinkMaterializer:
    SCORE_VERSION = GAP_LINK_SCORE_VERSION

    def __init__(
        self,
        settings: Settings,
        connection: Any = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.settings = settings
        self._connection = connection
        self._client = client or self._build_client()
        self._prompt_template = (
            self.settings.repo_root / "prompts" / "gap_linking" / "gap_item_link_v1.md"
        ).read_text()
        self._schema_path = (
            self.settings.repo_root / "schemas" / "derivations" / "gap_item_link.v1.schema.json"
        )
        self._schema = json.loads(self._schema_path.read_text())
        self._validator = Draft202012Validator(self._schema)
        vocab = json.loads(
            (self.settings.schema_root / "canonical" / "controlled_vocabularies.v1.json").read_text()
        )
        self._allowed_item_types = set(vocab.get("item_types") or [])

    def close(self) -> None:
        self._client.close()

    def refresh(
        self,
        *,
        gap_slugs: Optional[Sequence[str]] = None,
        item_slugs: Optional[Sequence[str]] = None,
        include_item_types: Optional[Sequence[str]] = None,
        exclude_item_types: Optional[Sequence[str]] = None,
        max_candidates_per_gap: int = DEFAULT_MAX_CANDIDATES_PER_GAP,
        max_links_per_gap: int = DEFAULT_MAX_LINKS_PER_GAP,
        refresh_item_details: bool = True,
    ) -> Dict[str, Any]:
        effective_item_types = self._resolve_item_types(include_item_types, exclude_item_types)
        conn, should_close = self._get_connection()
        affected_item_slugs: set[str] = set()
        linked_item_slugs: set[str] = set()
        llm_calls = 0
        inserted_link_count = 0

        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    item_facet_exists = self._table_exists(cursor, "item_facet")
                    replication_summary_exists = self._table_exists(cursor, "replication_summary")
                    gaps = self._fetch_gap_profiles(cursor, gap_slugs)
                    items = self._fetch_item_profiles(
                        cursor,
                        item_slugs,
                        effective_item_types,
                        item_facet_exists=item_facet_exists,
                        replication_summary_exists=replication_summary_exists,
                    )

                    if not gaps or not items:
                        return {
                            "score_version": self.SCORE_VERSION,
                            "selected_gap_count": len(gaps),
                            "selected_item_count": len(items),
                            "eligible_item_types": sorted(effective_item_types),
                            "inserted_link_count": 0,
                            "updated_item_count": 0,
                            "updated_gap_count": 0,
                            "materialization_summary": None,
                        }

                    gap_ids = [gap.gap_item_id for gap in gaps]
                    item_ids = [item.item_id for item in items]
                    affected_item_slugs.update(
                        self._fetch_existing_linked_item_slugs(cursor, gap_ids=gap_ids, item_ids=item_ids)
                    )
                    self._delete_existing_links(cursor, gap_ids=gap_ids, item_ids=item_ids)

                    for gap in gaps:
                        candidate_items = self._select_candidate_items(
                            gap,
                            items,
                            max_candidates=max_candidates_per_gap,
                        )
                        if not candidate_items:
                            continue
                        llm_calls += 1
                        response = self._request_gap_links(
                            gap=gap,
                            candidate_items=candidate_items,
                            max_links_per_gap=max_links_per_gap,
                        )
                        candidate_map = {item.slug: item for item in candidate_items}
                        normalized_links = self._normalize_links(
                            gap=gap,
                            response=response,
                            candidate_map=candidate_map,
                        )
                        inserted_link_count += self._upsert_gap_links(
                            cursor,
                            gap=gap,
                            links=normalized_links,
                            candidate_map=candidate_map,
                        )
                        linked_item_slugs.update(link["item_slug"] for link in normalized_links)

            materialization_summary = None
            if refresh_item_details:
                affected_item_slugs.update(linked_item_slugs)
                if affected_item_slugs:
                    materializer = ItemMaterializer(self.settings, conn)
                    materialization_summary = materializer.refresh(
                        item_slugs=sorted(affected_item_slugs),
                        include_related=False,
                    )
        finally:
            if should_close:
                conn.close()

        return {
            "score_version": self.SCORE_VERSION,
            "selected_gap_count": len(gaps),
            "selected_item_count": len(items),
            "eligible_item_types": sorted(effective_item_types),
            "llm_call_count": llm_calls,
            "inserted_link_count": inserted_link_count,
            "updated_item_count": len(affected_item_slugs),
            "updated_gap_count": len(gaps),
            "materialization_summary": materialization_summary,
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

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise GapLinkingError("DATABASE_URL is required to materialize gap links.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True

    def _resolve_item_types(
        self,
        include_item_types: Optional[Sequence[str]],
        exclude_item_types: Optional[Sequence[str]],
    ) -> set[str]:
        if include_item_types:
            item_types = {value for value in include_item_types if value in self._allowed_item_types}
        else:
            item_types = set(self._allowed_item_types)
            item_types.difference_update(DEFAULT_EXCLUDED_ITEM_TYPES)
        item_types.difference_update(value for value in (exclude_item_types or []) if value in item_types)
        return item_types

    def _fetch_gap_profiles(self, cursor: Any, gap_slugs: Optional[Sequence[str]]) -> List[GapProfile]:
        if gap_slugs:
            cursor.execute(
                """
                select
                  gi.id,
                  coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') as slug,
                  gi.title,
                  gf.name,
                  gi.payload,
                  gi.external_gap_item_id
                from gap_item gi
                left join gap_field gf on gf.id = gi.gap_field_id
                where coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') = any(%s)
                   or gi.external_gap_item_id = any(%s)
                order by gi.title asc
                """,
                (list(gap_slugs), list(gap_slugs)),
            )
        else:
            cursor.execute(
                """
                select
                  gi.id,
                  coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') as slug,
                  gi.title,
                  gf.name,
                  gi.payload,
                  gi.external_gap_item_id
                from gap_item gi
                left join gap_field gf on gf.id = gi.gap_field_id
                order by gi.title asc
                """
            )

        gaps: List[GapProfile] = []
        for row in cursor.fetchall():
            payload = row[4] or {}
            database_fields = payload.get("database_fields", {})
            description = (
                database_fields.get("description")
                or payload.get("evidence_text")
                or (
                    payload.get("claims", [{}])[0].get("claim_text_normalized")
                    if payload.get("claims")
                    else None
                )
            )
            cursor.execute(
                """
                select
                  gc.name,
                  gc.payload,
                  coalesce(
                    array(
                      select gr.title
                      from gap_capability_resource gcr
                      join gap_resource gr on gr.id = gcr.gap_resource_id
                      where gcr.gap_capability_id = gc.id
                      order by gr.title asc
                    ),
                    '{}'::text[]
                  ) as resource_titles
                from gap_item_capability gic
                join gap_capability gc on gc.id = gic.gap_capability_id
                where gic.gap_item_id = %s
                order by gc.name asc
                """,
                (row[0],),
            )
            capabilities = []
            for capability_row in cursor.fetchall():
                capability_payload = capability_row[1] or {}
                capabilities.append(
                    {
                        "name": capability_row[0],
                        "description": capability_payload.get("description"),
                        "tags": capability_payload.get("tags") or [],
                        "resources": list(capability_row[2] or []),
                    }
                )
            gaps.append(
                GapProfile(
                    gap_item_id=row[0],
                    slug=row[1] or row[5],
                    title=row[2],
                    field_name=row[3],
                    description=description,
                    tags=database_fields.get("tags") or [],
                    capabilities=capabilities,
                )
            )
        return gaps

    def _fetch_item_profiles(
        self,
        cursor: Any,
        item_slugs: Optional[Sequence[str]],
        item_types: set[str],
        *,
        item_facet_exists: bool,
        replication_summary_exists: bool,
    ) -> List[ItemProfile]:
        facet_hints_sql = (
            """
              coalesce(array(
                select concat(facet_name, ':', facet_value)
                from item_facet
                where item_id = ti.id
                order by facet_name asc, facet_value asc
              ), '{}'::text[]) as facet_hints,
            """
            if item_facet_exists
            else """
              '{}'::text[] as facet_hints,
            """
        )
        replication_sql = (
            """
              rs.replication_score,
              rs.practicality_score,
              rs.translatability_score,
              rs.primary_paper_count,
              rs.independent_primary_paper_count
            from toolkit_item ti
            left join replication_summary rs on rs.item_id = ti.id
            """
            if replication_summary_exists
            else """
              null::numeric as replication_score,
              null::numeric as practicality_score,
              null::numeric as translatability_score,
              null::int as primary_paper_count,
              null::int as independent_primary_paper_count
            from toolkit_item ti
            """
        )
        query = """
            select
              ti.id,
              ti.slug,
              ti.canonical_name,
              ti.item_type::text,
              ti.summary,
              ti.primary_input_modality::text,
              ti.primary_output_modality::text,
              coalesce(array(
                select mechanism_name
                from item_mechanism
                where item_id = ti.id
                order by mechanism_name asc
              ), '{}'::text[]) as mechanisms,
              coalesce(array(
                select technique_name
                from item_technique
                where item_id = ti.id
                order by technique_name asc
              ), '{}'::text[]) as techniques,
              coalesce(array(
                select target_process
                from item_target_process
                where item_id = ti.id
                order by target_process asc
              ), '{}'::text[]) as target_processes,
              coalesce(array(
                select synonym
                from item_synonym
                where item_id = ti.id
                order by synonym asc
              ), '{}'::text[]) as synonyms,
        """
        query += facet_hints_sql
        query += replication_sql
        query += """
            where ti.item_type::text = any(%s)
        """
        params: List[Any] = [sorted(item_types)]
        if item_slugs:
            query += " and ti.slug = any(%s)"
            params.append(list(item_slugs))
        query += " order by ti.canonical_name asc, ti.slug asc"
        cursor.execute(query, params)
        return [
            ItemProfile(
                item_id=row[0],
                slug=row[1],
                canonical_name=row[2],
                item_type=row[3],
                summary=row[4],
                primary_input_modality=row[5],
                primary_output_modality=row[6],
                mechanisms=list(row[7] or []),
                techniques=list(row[8] or []),
                target_processes=list(row[9] or []),
                synonyms=list(row[10] or []),
                facet_hints=list(row[11] or []),
                replication_summary={
                    "replication_score": float(row[12]) if row[12] is not None else None,
                    "practicality_score": float(row[13]) if row[13] is not None else None,
                    "translatability_score": float(row[14]) if row[14] is not None else None,
                    "primary_paper_count": row[15],
                    "independent_primary_paper_count": row[16],
                },
            )
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _table_exists(cursor: Any, table_name: str) -> bool:
        cursor.execute("select to_regclass(%s)", (table_name,))
        return cursor.fetchone()[0] is not None

    def _select_candidate_items(
        self,
        gap: GapProfile,
        items: Sequence[ItemProfile],
        *,
        max_candidates: int,
    ) -> List[ItemProfile]:
        ranked = sorted(
            items,
            key=lambda item: (
                self._prefilter_score(gap, item),
                item.replication_summary.get("replication_score") or 0.0,
                item.replication_summary.get("practicality_score") or 0.0,
                item.canonical_name.casefold(),
            ),
            reverse=True,
        )
        return ranked[: max(1, max_candidates)]

    @staticmethod
    def _prefilter_score(gap: GapProfile, item: ItemProfile) -> float:
        gap_text = gap.text_blob
        score = 0.0
        score += 3.0 * sum(1 for value in item.target_processes if value and value in gap_text)
        score += 2.0 * sum(1 for value in item.techniques if value.replace("_", " ") in gap_text)
        score += 2.0 * sum(1 for value in item.mechanisms if value.replace("_", " ") in gap_text)
        if item.primary_input_modality and item.primary_input_modality in gap_text:
            score += 1.25
        if item.primary_output_modality and item.primary_output_modality in gap_text:
            score += 1.5
        if item.item_type in {"engineering_method", "assay_method", "computation_method", "delivery_harness"}:
            score += 0.5
        token_overlap = len(gap.keyword_tokens.intersection(item.keyword_tokens))
        score += min(token_overlap, 8) * 0.35
        return round(score, 3)

    def _request_gap_links(
        self,
        *,
        gap: GapProfile,
        candidate_items: Sequence[ItemProfile],
        max_links_per_gap: int,
    ) -> Dict[str, Any]:
        schema_text = json.dumps(self._schema, indent=2)
        job = {
            "score_version": self.SCORE_VERSION,
            "max_links_per_gap": max_links_per_gap,
            "gap": gap.llm_payload(),
            "candidate_items": [item.llm_payload() for item in candidate_items],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are producing conservative, explainable gap-to-tool links for an evidence-first biology database. "
                    "Return only valid JSON. Do not invent evidence. "
                    "Only link collection items that are actionable tools, methods, assays, construct patterns, "
                    "multi-component systems, RNA elements, or delivery strategies for the stated gap."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{self._prompt_template}\n\n"
                    "## JSON Schema\n"
                    f"{schema_text}\n\n"
                    "## Gap Linking Job\n"
                    f"{json.dumps(job, indent=2)}\n"
                ),
            },
        ]
        response = self._request_validated_json(
            purpose=f"gap-link:{self.SCORE_VERSION}:{gap.slug}",
            messages=messages,
            gap_slug=gap.slug,
            allowed_item_slugs={item.slug for item in candidate_items},
        )
        return response

    def _request_validated_json(
        self,
        *,
        purpose: str,
        messages: List[Dict[str, str]],
        gap_slug: str,
        allowed_item_slugs: set[str],
    ) -> Dict[str, Any]:
        try:
            payload = run_cached_json_chat_completion(
                self.settings,
                self._client,
                purpose=purpose,
                messages=messages,
            )
        except LLMJSONCallError as exc:
            raise GapLinkingError(str(exc)) from exc

        last_error: Optional[str] = None
        current_payload = payload
        for _ in range(4):
            try:
                self._validate_response(
                    current_payload,
                    gap_slug=gap_slug,
                    allowed_item_slugs=allowed_item_slugs,
                )
                return current_payload
            except GapLinkingError as exc:
                last_error = str(exc)
                current_payload = self._repair_response(
                    original_messages=messages,
                    invalid_payload=current_payload,
                    validation_error=last_error,
                )
        raise GapLinkingError(
            f"Gap linking output could not be repaired to schema-valid JSON: {last_error}"
        )

    def _repair_response(
        self,
        *,
        original_messages: List[Dict[str, str]],
        invalid_payload: Dict[str, Any],
        validation_error: str,
    ) -> Dict[str, Any]:
        try:
            return run_cached_json_chat_completion(
                self.settings,
                self._client,
                purpose=f"gap-link-repair:{self.SCORE_VERSION}",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are repairing an invalid gap-linking JSON response. "
                            "Return only corrected JSON that exactly matches the schema and input constraints."
                        ),
                    },
                    *original_messages,
                    {
                        "role": "user",
                        "content": (
                            "## Invalid Response\n"
                            f"{json.dumps(invalid_payload, indent=2)}\n\n"
                            "## Validation Error\n"
                            f"{validation_error}\n"
                        ),
                    },
                ],
            )
        except LLMJSONCallError as exc:
            raise GapLinkingError(str(exc)) from exc

    def _validate_response(
        self,
        payload: Dict[str, Any],
        *,
        gap_slug: str,
        allowed_item_slugs: set[str],
    ) -> None:
        try:
            self._validator.validate(payload)
        except ValidationError as exc:
            path = ".".join(str(part) for part in exc.absolute_path) or "<root>"
            raise GapLinkingError(f"{path}: {exc.message}") from exc
        if payload.get("gap_slug") != gap_slug:
            raise GapLinkingError(f"gap_slug must be {gap_slug!r}.")
        seen = set()
        for entry in payload.get("candidate_links", []):
            item_slug = entry.get("item_slug")
            if item_slug not in allowed_item_slugs:
                raise GapLinkingError(f"Unknown or ineligible item_slug returned: {item_slug!r}.")
            if item_slug in seen:
                raise GapLinkingError(f"Duplicate item_slug returned: {item_slug!r}.")
            seen.add(item_slug)

    @staticmethod
    def _normalize_links(
        *,
        gap: GapProfile,
        response: Dict[str, Any],
        candidate_map: Dict[str, ItemProfile],
    ) -> List[Dict[str, Any]]:
        links: List[Dict[str, Any]] = []
        seen = set()
        for entry in response.get("candidate_links", []):
            item_slug = entry["item_slug"]
            if item_slug in seen or item_slug not in candidate_map:
                continue
            seen.add(item_slug)
            links.append(
                {
                    "gap_slug": gap.slug,
                    "item_slug": item_slug,
                    "mechanistic_match_score": _clamp_score(entry.get("mechanistic_match_score")),
                    "context_match_score": _clamp_score(entry.get("context_match_score")),
                    "throughput_match_score": _clamp_score(entry.get("throughput_match_score")),
                    "time_to_first_test_score": _clamp_score(entry.get("time_to_first_test_score")),
                    "cost_to_first_test_score": _clamp_score(entry.get("cost_to_first_test_score")),
                    "replication_confidence_modifier": _clamp_score(
                        entry.get("replication_confidence_modifier")
                    ),
                    "practicality_modifier": _clamp_score(entry.get("practicality_modifier")),
                    "translatability_modifier": _clamp_score(entry.get("translatability_modifier")),
                    "overall_gap_applicability_score": _clamp_score(
                        entry.get("overall_gap_applicability_score")
                    ),
                    "why_it_might_help": _normalize_text(entry.get("why_it_might_help")),
                    "assumptions": _normalize_text(entry.get("assumptions")),
                    "missing_evidence": _normalize_text(entry.get("missing_evidence")),
                }
            )
        return links

    def _upsert_gap_links(
        self,
        cursor: Any,
        *,
        gap: GapProfile,
        links: Sequence[Dict[str, Any]],
        candidate_map: Dict[str, ItemProfile],
    ) -> int:
        inserted = 0
        for link in links:
            item = candidate_map[link["item_slug"]]
            cursor.execute(
                """
                insert into item_gap_link (
                  item_id,
                  gap_item_id,
                  score_version,
                  mechanistic_match_score,
                  context_match_score,
                  throughput_match_score,
                  time_to_first_test_score,
                  cost_to_first_test_score,
                  replication_confidence_modifier,
                  practicality_modifier,
                  translatability_modifier,
                  overall_gap_applicability_score,
                  why_it_might_help,
                  assumptions,
                  missing_evidence
                )
                values (
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                on conflict (item_id, gap_item_id, score_version) do update
                set
                  mechanistic_match_score = excluded.mechanistic_match_score,
                  context_match_score = excluded.context_match_score,
                  throughput_match_score = excluded.throughput_match_score,
                  time_to_first_test_score = excluded.time_to_first_test_score,
                  cost_to_first_test_score = excluded.cost_to_first_test_score,
                  replication_confidence_modifier = excluded.replication_confidence_modifier,
                  practicality_modifier = excluded.practicality_modifier,
                  translatability_modifier = excluded.translatability_modifier,
                  overall_gap_applicability_score = excluded.overall_gap_applicability_score,
                  why_it_might_help = excluded.why_it_might_help,
                  assumptions = excluded.assumptions,
                  missing_evidence = excluded.missing_evidence
                """,
                (
                    item.item_id,
                    gap.gap_item_id,
                    self.SCORE_VERSION,
                    link["mechanistic_match_score"],
                    link["context_match_score"],
                    link["throughput_match_score"],
                    link["time_to_first_test_score"],
                    link["cost_to_first_test_score"],
                    link["replication_confidence_modifier"],
                    link["practicality_modifier"],
                    link["translatability_modifier"],
                    link["overall_gap_applicability_score"],
                    link["why_it_might_help"],
                    link["assumptions"] or None,
                    link["missing_evidence"] or None,
                ),
            )
            inserted += 1
        return inserted

    def _delete_existing_links(
        self,
        cursor: Any,
        *,
        gap_ids: Sequence[Any],
        item_ids: Sequence[Any],
    ) -> None:
        cursor.execute(
            """
            delete from item_gap_link
            where score_version = %s
              and gap_item_id = any(%s)
              and item_id = any(%s)
            """,
            (self.SCORE_VERSION, list(gap_ids), list(item_ids)),
        )

    def _fetch_existing_linked_item_slugs(
        self,
        cursor: Any,
        *,
        gap_ids: Sequence[Any],
        item_ids: Sequence[Any],
    ) -> set[str]:
        cursor.execute(
            """
            select distinct ti.slug
            from item_gap_link igl
            join toolkit_item ti on ti.id = igl.item_id
            where igl.score_version = %s
              and igl.gap_item_id = any(%s)
              and igl.item_id = any(%s)
            """,
            (self.SCORE_VERSION, list(gap_ids), list(item_ids)),
        )
        return {row[0] for row in cursor.fetchall()}
