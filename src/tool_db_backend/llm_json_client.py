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

_CACHE_VERSION = "chat-completions-json-v1"
_RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class LLMJSONCallError(RuntimeError):
    pass


def run_cached_json_chat_completion(
    settings: Settings,
    client: httpx.Client,
    *,
    purpose: str,
    messages: List[Dict[str, str]],
    temperature: float = 0,
    response_format: Optional[Dict[str, Any]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Dict[str, Any]:
    request_body = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "response_format": response_format or {"type": "json_object"},
    }
    cache_key = _build_cache_key(settings, purpose, request_body)
    cache_path = settings.llm_cache_root / _CACHE_VERSION / f"{cache_key}.json"

    if settings.llm_cache_enabled:
        cached = _read_cache_entry(cache_path)
        if cached is not None:
            return cached

    if not settings.llm_api_key:
        raise LLMJSONCallError("LLM API key is not configured and no cached response was found.")

    last_error: Optional[Exception] = None
    for attempt in range(1, settings.llm_retry_attempts + 1):
        response: Optional[httpx.Response] = None
        try:
            response = client.post("/chat/completions", json=request_body)
            response.raise_for_status()
            response_payload = response.json()
            parsed_json = _parse_json_object_response(response_payload)
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
                raise LLMJSONCallError(f"LLM request failed with status {exc.response.status_code}.") from exc
        except (httpx.RequestError, json.JSONDecodeError, LLMJSONCallError) as exc:
            last_error = exc
            if attempt >= settings.llm_retry_attempts:
                raise LLMJSONCallError("LLM request failed after retries.") from exc

        sleep_fn(_retry_delay_seconds(settings, attempt, response))

    raise LLMJSONCallError("LLM request failed after retries.") from last_error


def _build_cache_key(settings: Settings, purpose: str, request_body: Dict[str, Any]) -> str:
    canonical_payload = {
        "cache_version": _CACHE_VERSION,
        "base_url": str(settings.llm_base_url).rstrip("/"),
        "endpoint": "/chat/completions",
        "purpose": purpose,
        "request_body": request_body,
    }
    rendered = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _parse_json_object_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMJSONCallError("Unexpected LLM response shape.") from exc

    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise LLMJSONCallError("LLM JSON response was not an object.")
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
