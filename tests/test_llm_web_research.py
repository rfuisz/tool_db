import json
from pathlib import Path

import httpx

from tool_db_backend.config import get_settings
from tool_db_backend.llm_web_research import LLMWebResearchClient


def test_llm_web_research_client_uses_responses_api_and_cache(tmp_path: Path) -> None:
    response_payload = {
        "summary": "AM1_C0023g2 is a cyanobacteriochrome photoreceptor used in optogenetic switching.",
        "high_signal_sources": [
            {
                "title": "Green, orange, red, and far-red optogenetic tools derived from cyanobacteriochromes",
                "url": "https://example.test/paper",
                "source_type": "preprint",
                "publication_year": 2019,
                "doi": "10.1101/769422",
                "pmid": None,
                "why_relevant": "Describes optogenetic binders and application context for Am1_c0023g2.",
            }
        ],
        "related_item_candidates": [
            {
                "name": "Amg2",
                "relation": "engineered_variant",
                "why_relevant": "An engineered truncation used in cyanobacteriochrome-based switching systems.",
            }
        ],
        "open_questions": [],
    }
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert request.url.path.endswith("/responses")
        payload = json.loads(request.read().decode("utf-8"))
        assert payload["tools"] == [{"type": "web_search_preview"}]
        return httpx.Response(200, json={"output_text": json.dumps(response_payload)})

    settings = get_settings().model_copy(
        update={
            "llm_api_key": "test-key",
            "llm_base_url": "https://example.test/v1",
            "llm_web_research_enabled": True,
            "llm_web_research_model": "gpt-5.4",
            "repo_root": tmp_path,
        }
    )
    client = LLMWebResearchClient(
        settings,
        client=httpx.Client(
            base_url=settings.effective_llm_web_research_base_url,
            transport=httpx.MockTransport(handler),
        ),
    )

    first = client.research_source_document(
        source_document={
            "title": "Photoconversion and Fluorescence Properties of AM1_C0023g2",
            "doi": "10.1000/example",
            "pmid": "12345678",
            "source_type": "primary_paper",
        },
        abstract_text="Example abstract",
    )
    second = client.research_source_document(
        source_document={
            "title": "Photoconversion and Fluorescence Properties of AM1_C0023g2",
            "doi": "10.1000/example",
            "pmid": "12345678",
            "source_type": "primary_paper",
        },
        abstract_text="Example abstract",
    )
    client.close()

    assert first["summary"].startswith("AM1_C0023g2")
    assert second["related_item_candidates"][0]["name"] == "Amg2"
    assert request_count == 1
