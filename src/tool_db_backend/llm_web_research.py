from __future__ import annotations

import hashlib
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from tool_db_backend.config import Settings

_CACHE_VERSION = "responses-web-research-v1"
_RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}

_WEB_RESEARCH_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "high_signal_sources": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "source_type": {"type": "string"},
                    "publication_year": {"type": ["integer", "null"]},
                    "doi": {"type": ["string", "null"]},
                    "pmid": {"type": ["string", "null"]},
                    "why_relevant": {"type": "string"},
                },
                "required": ["title", "url", "source_type", "publication_year", "doi", "pmid", "why_relevant"],
            },
        },
        "related_item_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "relation": {"type": "string"},
                    "why_relevant": {"type": "string"},
                },
                "required": ["name", "relation", "why_relevant"],
            },
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "high_signal_sources", "related_item_candidates", "open_questions"],
}

_QUERY_EXPANSION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "related_item_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "relation": {"type": "string"},
                    "why_relevant": {"type": "string"},
                },
                "required": ["name", "relation", "why_relevant"],
            },
        },
        "literature_queries": {"type": "array", "items": {"type": "string"}},
        "optobase_queries": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["related_item_candidates", "literature_queries", "optobase_queries"],
}


class LLMWebResearchError(RuntimeError):
    pass


class LLMWebResearchClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        self._client = client or self._build_client()

    def close(self) -> None:
        self._client.close()

    def research_source_document(
        self,
        *,
        source_document: Dict[str, Any],
        abstract_text: str = "",
    ) -> Dict[str, Any]:
        if not self.settings.llm_web_research_enabled:
            return {}
        if not self.settings.effective_llm_web_research_api_key:
            raise LLMWebResearchError("Web research is enabled but no API key is configured.")

        title = str(source_document.get("title") or "").strip()
        if not title:
            return {}
        prompt_payload = {
            "title": title,
            "source_type": source_document.get("source_type"),
            "doi": source_document.get("doi"),
            "pmid": source_document.get("pmid"),
            "publication_year": source_document.get("publication_year"),
            "journal_or_source": source_document.get("journal_or_source"),
            "abstract_text": abstract_text or source_document.get("abstract_text") or "",
        }
        return run_cached_web_research(
            self.settings,
            self._client,
            purpose="literature_web_research",
            prompt_payload=prompt_payload,
            schema=_WEB_RESEARCH_SCHEMA,
        )

    def expand_seed_queries(
        self,
        *,
        seed_terms: List[str],
        max_related_items: int = 24,
    ) -> Dict[str, Any]:
        if not self.settings.llm_web_research_enabled:
            return {}
        if not self.settings.effective_llm_web_research_api_key:
            raise LLMWebResearchError("Web research is enabled but no API key is configured.")
        cleaned_terms = [term.strip() for term in seed_terms if term and term.strip()]
        if not cleaned_terms:
            return {}
        prompt_payload = {
            "seed_terms": cleaned_terms,
            "max_related_items": max_related_items,
            "goal": (
                "Expand these toolkit seed terms into adjacent tools, components, and literature search queries "
                "that are well-supported in optogenetics and related biocontrol literature."
            ),
            "naming_requirement": (
                "For related_item_candidates.name, return the actual tool/component/system name only "
                "(for example AsLOV2, iLID, CRY2/CIB1, Am1_c0023g2, PhyB/PIF), not paper titles."
            ),
        }
        return run_cached_web_research(
            self.settings,
            self._client,
            purpose="seed_query_expansion",
            prompt_payload=prompt_payload,
            schema=_QUERY_EXPANSION_SCHEMA,
        )

    def _build_client(self) -> httpx.Client:
        headers = {
            "Authorization": f"Bearer {self.settings.effective_llm_web_research_api_key}",
            "Content-Type": "application/json",
        }
        return httpx.Client(
            base_url=self.settings.effective_llm_web_research_base_url,
            headers=headers,
            timeout=180.0,
        )


def run_cached_web_research(
    settings: Settings,
    client: httpx.Client,
    *,
    purpose: str,
    prompt_payload: Dict[str, Any],
    schema: Dict[str, Any],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    request_body = {
        "model": settings.effective_llm_web_research_model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a literature-enrichment assistant for an evidence-first biology database. "
                            "Use web search to find additional high-signal sources about the same tool, component, or paper topic. "
                            "Prioritize peer-reviewed primary papers, reviews, protocol pages, and database entries over tertiary summaries. "
                            "Return only schema-valid JSON. Do not invent citations, DOIs, PMIDs, or related tools."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Research the following source document and compile additional source leads that could enrich downstream extraction. "
                            "Use the title/DOI/PMID/abstract as anchors, and include related tool or component names only when they are explicitly supported by the discovered sources.\n\n"
                            f"{json.dumps(prompt_payload, indent=2)}"
                        ),
                    }
                ],
            },
        ],
        "tools": [{"type": "web_search_preview"}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "web_research_summary",
                "schema": schema,
                "strict": True,
            }
        },
    }
    cache_key = _build_cache_key(settings, purpose, request_body)
    cache_path = settings.llm_cache_root / _CACHE_VERSION / f"{cache_key}.json"

    if settings.llm_cache_enabled:
        cached = _read_cache_entry(cache_path)
        if cached is not None:
            return cached

    last_error: Optional[Exception] = None
    for attempt in range(1, settings.llm_retry_attempts + 1):
        response: Optional[httpx.Response] = None
        try:
            response = client.post("/responses", json=request_body)
            response.raise_for_status()
            response_payload = response.json()
            parsed_json = _parse_response_json(response_payload)
            if settings.llm_cache_enabled:
                _write_cache_entry(
                    cache_path=cache_path,
                    purpose=purpose,
                    request_body=request_body,
                    response_payload=response_payload,
                    parsed_json=parsed_json,
                )
            return parsed_json
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code not in _RETRYABLE_STATUS_CODES or attempt >= settings.llm_retry_attempts:
                raise LLMWebResearchError(
                    f"Web research request failed with status {exc.response.status_code}."
                ) from exc
        except (httpx.RequestError, json.JSONDecodeError, LLMWebResearchError) as exc:
            last_error = exc
            if attempt >= settings.llm_retry_attempts:
                raise LLMWebResearchError("Web research request failed after retries.") from exc
        sleep_fn(_retry_delay_seconds(settings, attempt, response))
    raise LLMWebResearchError("Web research request failed after retries.") from last_error


def _build_cache_key(settings: Settings, purpose: str, request_body: Dict[str, Any]) -> str:
    canonical_payload = {
        "cache_version": _CACHE_VERSION,
        "base_url": str(settings.effective_llm_web_research_base_url).rstrip("/"),
        "endpoint": "/responses",
        "purpose": purpose,
        "request_body": request_body,
    }
    rendered = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _parse_response_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return _parse_json_string(payload["output_text"])

    for item in payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text_value = content.get("text") or content.get("output_text")
            if isinstance(text_value, str) and text_value.strip():
                return _parse_json_string(text_value)

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMWebResearchError("Unexpected web research response shape.") from exc
    return _parse_json_string(content)


def _parse_json_string(content: str) -> Dict[str, Any]:
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise LLMWebResearchError("Web research response was not a JSON object.")
    return parsed


def _read_cache_entry(cache_path: Path) -> Optional[Dict[str, Any]]:
    if not cache_path.exists():
        return None
    try:
        cache_entry = json.loads(cache_path.read_text())
        parsed_json = cache_entry["parsed_json"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed_json, dict):
        return None
    return parsed_json


def _write_cache_entry(
    *,
    cache_path: Path,
    purpose: str,
    request_body: Dict[str, Any],
    response_payload: Dict[str, Any],
    parsed_json: Dict[str, Any],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "cache_version": _CACHE_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": purpose,
        "request_body": request_body,
        "response_payload": response_payload,
        "parsed_json": parsed_json,
    }
    temp_path = cache_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(entry, indent=2) + "\n")
    temp_path.replace(cache_path)


def _retry_delay_seconds(settings: Settings, attempt: int, response: Optional[httpx.Response]) -> float:
    retry_after = _parse_retry_after_seconds(response)
    if retry_after is not None:
        return min(retry_after, settings.llm_retry_max_delay_seconds)
    base_delay = settings.llm_retry_base_delay_seconds * (2 ** (attempt - 1))
    jitter = random.uniform(0, settings.llm_retry_base_delay_seconds / 4)
    return min(base_delay + jitter, settings.llm_retry_max_delay_seconds)


def _parse_retry_after_seconds(response: Optional[httpx.Response]) -> Optional[float]:
    if response is None:
        return None
    raw_value = response.headers.get("Retry-After")
    if raw_value is None:
        return None
    try:
        parsed = float(raw_value)
    except ValueError:
        return None
    return max(parsed, 0.0)
