"""LLM-powered synthesis of item explainers, summaries, and metadata.

Reads claims, evidence, and extraction context from the DB, then asks the
configured LLM to produce a coherent structured profile for each item.
Results are written back as explainers and summary updates.
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

from tool_db_backend.config import Settings
from tool_db_backend.llm_json_client import (
    LLMJSONCallError,
    run_cached_json_chat_completion,
)
from tool_db_backend.pipeline_versions import MATERIALIZATION_VERSION

logger = logging.getLogger(__name__)

_SYNTHESIS_PURPOSE_PREFIX = "item-profile-synthesis"
_SYNTHESIS_VERSION = "synth_v1"
_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "materialization" / "synthesize_item_profile_v1.md"


def _build_evidence_block(context_row: Dict[str, Any]) -> str:
    """Format the evidence for a single item into a prompt-friendly text block."""
    parts: List[str] = []

    parts.append(f"Tool name: {context_row['canonical_name']}")
    parts.append(f"Type: {context_row['item_type']}")
    if context_row.get("summary"):
        parts.append(f"Current summary: {context_row['summary']}")
    if context_row.get("synonyms"):
        parts.append(f"Synonyms: {', '.join(context_row['synonyms'][:5])}")
    if context_row.get("mechanisms"):
        parts.append(f"Known mechanisms: {', '.join(context_row['mechanisms'])}")
    if context_row.get("techniques"):
        parts.append(f"Known techniques: {', '.join(context_row['techniques'])}")
    if context_row.get("target_processes"):
        parts.append(f"Target processes: {', '.join(context_row['target_processes'])}")
    if context_row.get("input_modality"):
        parts.append(f"Input modality: {context_row['input_modality']}")
    if context_row.get("output_modality"):
        parts.append(f"Output modality: {context_row['output_modality']}")

    claims = context_row.get("claims", [])
    if claims:
        parts.append(f"\n--- Claims from source literature ({len(claims)} total) ---")
        for i, claim in enumerate(claims[:20], 1):
            claim_type = claim.get("claim_type", "unknown")
            text = claim.get("claim_text_normalized", "")
            source_title = claim.get("source_title", "")
            if text:
                source_tag = f" [from: {source_title}]" if source_title else ""
                parts.append(f"  {i}. [{claim_type}] {text}{source_tag}")

    evidence_texts = context_row.get("evidence_texts", [])
    if evidence_texts:
        parts.append(f"\n--- Extraction evidence texts ---")
        for text in evidence_texts[:5]:
            parts.append(f"  - {text}")

    freeform = context_row.get("freeform_explainers", {})
    if freeform:
        parts.append(f"\n--- Freeform explainers from extraction ---")
        for key, value in freeform.items():
            if value:
                parts.append(f"  {key}: {value}")

    citations = context_row.get("citations", [])
    if citations:
        parts.append(f"\n--- Source citations ({len(citations)}) ---")
        for cit in citations[:10]:
            year = cit.get("publication_year", "?")
            journal = cit.get("journal", "")
            parts.append(f"  - {cit.get('title', '?')} ({year}) {journal}")

    return "\n".join(parts)


def _load_prompt_template() -> str:
    return _PROMPT_PATH.read_text()


def synthesize_item_profile(
    settings: Settings,
    client: httpx.Client,
    context_row: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Call the LLM to synthesize a structured profile for one item."""
    slug = context_row["slug"]
    evidence_block = _build_evidence_block(context_row)

    if len(evidence_block) < 100:
        logger.debug("Skipping LLM synthesis for %s: insufficient evidence.", slug)
        return None

    system_prompt = _load_prompt_template()
    user_message = (
        f"Produce a structured JSON profile for this biological tool.\n\n"
        f"{evidence_block}"
    )

    purpose = f"{_SYNTHESIS_PURPOSE_PREFIX}:{_SYNTHESIS_VERSION}:{slug}"

    try:
        result = run_cached_json_chat_completion(
            settings,
            client,
            purpose=purpose,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        return result
    except LLMJSONCallError:
        logger.warning("LLM synthesis failed for %s, falling back to heuristic.", slug)
        return None


def fetch_synthesis_contexts(cursor: Any, item_ids: Sequence[Any]) -> Dict[Any, Dict[str, Any]]:
    """Batch-fetch all data needed for LLM synthesis for a set of items."""
    if not item_ids:
        return {}

    id_list = list(item_ids)
    cursor.execute(
        """
        select
          ti.id, ti.slug, ti.canonical_name, ti.item_type::text, ti.summary,
          ti.primary_input_modality::text, ti.primary_output_modality::text,
          coalesce(array(select synonym from item_synonym where item_id = ti.id), '{}'::text[]) as synonyms,
          coalesce(array(select mechanism_name from item_mechanism where item_id = ti.id), '{}'::text[]) as mechanisms,
          coalesce(array(select technique_name from item_technique where item_id = ti.id), '{}'::text[]) as techniques,
          coalesce(array(select target_process from item_target_process where item_id = ti.id), '{}'::text[]) as target_processes
        from toolkit_item ti
        where ti.id = any(%s)
        """,
        (id_list,),
    )
    base_rows = {}
    for row in cursor.fetchall():
        base_rows[row[0]] = {
            "item_id": row[0],
            "slug": row[1],
            "canonical_name": row[2],
            "item_type": row[3],
            "summary": row[4],
            "input_modality": row[5],
            "output_modality": row[6],
            "synonyms": list(row[7] or []),
            "mechanisms": list(row[8] or []),
            "techniques": list(row[9] or []),
            "target_processes": list(row[10] or []),
        }

    for item_id in base_rows:
        cursor.execute(
            """
            select ec.claim_type, ec.claim_text_normalized, sd.title
            from extracted_claim ec
            join claim_subject_link csl on csl.claim_id = ec.id
            join source_document sd on sd.id = ec.source_document_id
            where csl.item_id = %s
            order by sd.publication_year desc nulls last, ec.claim_type
            limit 25
            """,
            (item_id,),
        )
        seen_texts = set()
        claims = []
        for row in cursor.fetchall():
            text = (row[1] or "").strip()
            if text and text.casefold() not in seen_texts:
                seen_texts.add(text.casefold())
                claims.append({
                    "claim_type": row[0],
                    "claim_text_normalized": text,
                    "source_title": row[2],
                })
        base_rows[item_id]["claims"] = claims

        cursor.execute(
            """
            select eic.evidence_text, eic.raw_payload
            from extracted_item_candidate eic
            where eic.matched_item_id = %s
            limit 5
            """,
            (item_id,),
        )
        evidence_texts = []
        freeform = {}
        for row in cursor.fetchall():
            if row[0]:
                evidence_texts.append(row[0])
            rp = row[1] or {}
            for key, val in rp.get("freeform_explainers", {}).items():
                if val and key not in freeform:
                    freeform[key] = val
        base_rows[item_id]["evidence_texts"] = evidence_texts
        base_rows[item_id]["freeform_explainers"] = freeform

        cursor.execute(
            """
            select sd.title, sd.publication_year, sd.journal_or_source
            from item_citation ic
            join source_document sd on sd.id = ic.source_document_id
            where ic.item_id = %s
            order by ic.importance_rank
            limit 10
            """,
            (item_id,),
        )
        base_rows[item_id]["citations"] = [
            {"title": row[0], "publication_year": row[1], "journal": row[2]}
            for row in cursor.fetchall()
        ]

    return base_rows


def run_llm_synthesis_batch(
    settings: Settings,
    cursor: Any,
    item_ids: Sequence[Any],
) -> Dict[str, Any]:
    """Run LLM synthesis for a batch of items in parallel, then write results to DB."""
    # Skip items that already have LLM synthesis and no new evidence
    cursor.execute(
        """select ti.id from toolkit_item ti
           where ti.id = any(%s)
             and ti.summary_derivation_model is not null
             and ti.materialization_evidence_hash is not null
             and ti.materialization_evidence_hash = (
               select materialization_evidence_hash from toolkit_item where id = ti.id
             )
             and exists (
               select 1 from item_explainer ie
               where ie.item_id = ti.id and ie.derivation_model is not null
             )
        """,
        (list(item_ids),),
    )
    already_synthesized = {row[0] for row in cursor.fetchall()}
    ids_needing_synthesis = [iid for iid in item_ids if iid not in already_synthesized]
    pre_skipped = len(already_synthesized)
    if pre_skipped:
        logger.info("Skipping %d items already synthesized with current evidence hash.", pre_skipped)

    contexts = fetch_synthesis_contexts(cursor, ids_needing_synthesis)
    if not contexts:
        return {"synthesized": 0, "skipped": pre_skipped, "failed": 0}

    model_name = settings.llm_model
    synthesized = 0
    skipped = pre_skipped
    failed = 0

    results: Dict[Any, Dict[str, Any]] = {}

    def _synth_one(item_id: Any) -> Tuple[Any, Optional[Dict[str, Any]]]:
        ctx = contexts[item_id]
        with httpx.Client(
            base_url=settings.llm_base_url,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            timeout=120,
        ) as client:
            return item_id, synthesize_item_profile(settings, client, ctx)

    with ThreadPoolExecutor(max_workers=settings.llm_max_concurrency) as pool:
        futures = {pool.submit(_synth_one, iid): iid for iid in contexts}
        for i, future in enumerate(as_completed(futures), 1):
            item_id = futures[future]
            try:
                _, profile = future.result()
                if profile:
                    results[item_id] = profile
                    synthesized += 1
                else:
                    skipped += 1
            except Exception:
                logger.warning("LLM synthesis failed for item %s", item_id, exc_info=True)
                failed += 1
            if i == 1 or i % 100 == 0 or i == len(futures):
                logger.info("LLM synthesis progress: %s/%s", i, len(futures))

    applied = 0
    apply_errors = 0
    for item_id, profile in results.items():
        ctx = contexts[item_id]
        try:
            _apply_synthesis_result(cursor, item_id, ctx["slug"], profile, model_name)
            applied += 1
        except Exception:
            logger.warning("Failed to apply synthesis for %s", ctx["slug"], exc_info=True)
            apply_errors += 1

    logger.info(
        "LLM synthesis complete: synthesized=%s skipped=%s failed=%s",
        synthesized, skipped, failed,
    )
    return {"synthesized": synthesized, "skipped": skipped, "failed": failed}


def _sanitize_text(text: str) -> str:
    """Remove NUL bytes and other problematic characters from LLM output."""
    return text.replace("\x00", "")


def _apply_synthesis_result(
    cursor: Any,
    item_id: Any,
    slug: str,
    profile: Dict[str, Any],
    model_name: str,
) -> None:
    """Write the LLM-synthesized profile into the DB tables."""
    version = MATERIALIZATION_VERSION

    new_summary = _sanitize_text((profile.get("summary") or "").strip())
    if new_summary and len(new_summary) > 20:
        cursor.execute(
            "update toolkit_item set summary = %s, summary_derivation_model = %s where id = %s",
            (new_summary, model_name, item_id),
        )

    explainer_map = {
        "usefulness": ("Why this is useful", profile.get("usefulness")),
        "problem_solved": ("What problem this helps solve", profile.get("problem_solved")),
        "strengths": ("Strengths", profile.get("strengths")),
        "limitations": ("Limitations", profile.get("limitations")),
        "implementation_constraints": ("Implementation constraints", profile.get("implementation_notes")),
    }

    for kind, (title, body) in explainer_map.items():
        body_text = _sanitize_text((body or "").strip())
        if not body_text or len(body_text) < 15:
            continue
        evidence = json.dumps({"synthesis_source": "llm", "synthesis_version": _SYNTHESIS_VERSION})
        cursor.execute(
            """
            insert into item_explainer (
              item_id, explainer_kind, title, body, evidence_payload,
              derived_version, derivation_model, updated_at
            )
            values (%s, %s, %s, %s, %s::jsonb, %s, %s, now())
            on conflict (item_id, explainer_kind)
              do update set body = excluded.body, title = excluded.title,
                derived_version = excluded.derived_version,
                derivation_model = excluded.derivation_model,
                evidence_payload = excluded.evidence_payload,
                updated_at = now()
            """,
            (item_id, kind, title, body_text, evidence, version, model_name),
        )

    new_mechanisms = profile.get("mechanisms") or []
    if isinstance(new_mechanisms, list) and new_mechanisms:
        for mech in new_mechanisms[:10]:
            mech_name = _sanitize_text(str(mech).strip().lower())
            if mech_name and len(mech_name) > 2:
                cursor.execute(
                    "insert into item_mechanism (item_id, mechanism_name) values (%s, %s) on conflict do nothing",
                    (item_id, mech_name),
                )

    new_techniques = profile.get("techniques") or []
    if isinstance(new_techniques, list) and new_techniques:
        for tech in new_techniques[:10]:
            tech_name = _sanitize_text(str(tech).strip().lower())
            if tech_name and len(tech_name) > 2:
                cursor.execute(
                    "insert into item_technique (item_id, technique_name) values (%s, %s) on conflict do nothing",
                    (item_id, tech_name),
                )
