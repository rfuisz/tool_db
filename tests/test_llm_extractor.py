import json
from pathlib import Path

import httpx

from tool_db_backend.config import get_settings
from tool_db_backend.llm_extractor import LLMExtractionRunner


def test_llm_extractor_runs_job_and_writes_packet(tmp_path: Path) -> None:
    job_path = tmp_path / "job.json"
    prompt_dir = tmp_path / "prompts" / "extraction"
    schema_dir = tmp_path / "schemas" / "extraction"
    prompt_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)

    prompt_path = prompt_dir / "primary_paper_extract_v1.md"
    prompt_path.write_text("Extract a packet.")

    schema_src = Path("schemas/extraction/primary_paper_extract.v1.schema.json")
    common_src = Path("schemas/extraction/common.v1.schema.json")
    (schema_dir / "primary_paper_extract.v1.schema.json").write_text(schema_src.read_text())
    (schema_dir / "common.v1.schema.json").write_text(common_src.read_text())

    job = {
        "job_type": "llm_extraction_job_v1",
        "target_packet_type": "primary_paper_extract_v1",
        "prompt_template": "prompts/extraction/primary_paper_extract_v1.md",
        "schema_path": "schemas/extraction/primary_paper_extract.v1.schema.json",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "input_context": {
            "title": "Example paper",
            "abstract_text": "Example abstract",
        },
    }
    job_path.write_text(json.dumps(job))

    response_packet = {
        "packet_type": "primary_paper_extract_v1",
        "schema_version": "v1",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "entity_candidates": [],
        "claims": [],
        "validation_observations": [],
        "replication_signals": {},
        "unresolved_ambiguities": [],
    }

    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(response_packet)
                        }
                    }
                ]
            },
        )

    settings = get_settings().model_copy(
        update={
            "repo_root": tmp_path,
            "llm_api_key": "test-key",
            "llm_base_url": "https://example.test/v1",
        }
    )
    runner = LLMExtractionRunner(
        settings,
        client=httpx.Client(base_url=settings.llm_base_url, transport=httpx.MockTransport(handler)),
    )

    result = runner.run_job_file(job_path)
    cached_result = runner.run_job_file(job_path)
    prompt_path.write_text("Extract a packet with updated wording.")
    invalidated_result = runner.run_job_file(job_path)
    runner.close()

    assert result["packet_type"] == "primary_paper_extract_v1"
    assert cached_result["packet_type"] == "primary_paper_extract_v1"
    assert invalidated_result["packet_type"] == "primary_paper_extract_v1"
    assert Path(result["output_path"]).exists()
    assert request_count == 2


def test_llm_extractor_repairs_invalid_first_response(tmp_path: Path) -> None:
    job_path = tmp_path / "job.json"
    prompt_dir = tmp_path / "prompts" / "extraction"
    schema_dir = tmp_path / "schemas" / "extraction"
    prompt_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)

    (prompt_dir / "primary_paper_extract_v1.md").write_text("Extract a packet.")
    schema_src = Path("schemas/extraction/primary_paper_extract.v1.schema.json")
    common_src = Path("schemas/extraction/common.v1.schema.json")
    (schema_dir / "primary_paper_extract.v1.schema.json").write_text(schema_src.read_text())
    (schema_dir / "common.v1.schema.json").write_text(common_src.read_text())

    job = {
        "job_type": "llm_extraction_job_v1",
        "target_packet_type": "primary_paper_extract_v1",
        "prompt_template": "prompts/extraction/primary_paper_extract_v1.md",
        "schema_path": "schemas/extraction/primary_paper_extract.v1.schema.json",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "input_context": {
            "title": "Example paper",
            "abstract_text": "Example abstract",
        },
    }
    job_path.write_text(json.dumps(job))

    invalid_packet = {
        "packet_type": "primary_paper_extract_v1",
        "schema_version": "v1",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "entity_candidates": [
            {"name": "Bad Entity", "entity_type": "research_topic", "source_text": "Bad Entity"}
        ],
        "claims": [],
        "validation_observations": [],
        "replication_signals": {},
        "unresolved_ambiguities": [],
    }
    valid_packet = {
        "packet_type": "primary_paper_extract_v1",
        "schema_version": "v1",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "entity_candidates": [],
        "claims": [],
        "validation_observations": [],
        "replication_signals": {},
        "unresolved_ambiguities": [],
    }

    responses = iter(
        [
            {"choices": [{"message": {"content": json.dumps(invalid_packet)}}]},
            {"choices": [{"message": {"content": json.dumps(valid_packet)}}]},
        ]
    )
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, json=next(responses))

    settings = get_settings().model_copy(
        update={
            "repo_root": tmp_path,
            "llm_api_key": "test-key",
            "llm_base_url": "https://example.test/v1",
        }
    )
    runner = LLMExtractionRunner(
        settings,
        client=httpx.Client(base_url=settings.llm_base_url, transport=httpx.MockTransport(handler)),
    )

    result = runner.run_job_file(job_path)
    cached_result = runner.run_job_file(job_path)
    runner.close()

    assert result["packet_type"] == "primary_paper_extract_v1"
    assert cached_result["packet_type"] == "primary_paper_extract_v1"
    assert Path(result["output_path"]).exists()
    assert request_count == 2


def test_llm_extractor_retries_retryable_failures(tmp_path: Path) -> None:
    job_path = tmp_path / "job.json"
    prompt_dir = tmp_path / "prompts" / "extraction"
    schema_dir = tmp_path / "schemas" / "extraction"
    prompt_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)

    (prompt_dir / "primary_paper_extract_v1.md").write_text("Extract a packet.")
    schema_src = Path("schemas/extraction/primary_paper_extract.v1.schema.json")
    common_src = Path("schemas/extraction/common.v1.schema.json")
    (schema_dir / "primary_paper_extract.v1.schema.json").write_text(schema_src.read_text())
    (schema_dir / "common.v1.schema.json").write_text(common_src.read_text())

    job = {
        "job_type": "llm_extraction_job_v1",
        "target_packet_type": "primary_paper_extract_v1",
        "prompt_template": "prompts/extraction/primary_paper_extract_v1.md",
        "schema_path": "schemas/extraction/primary_paper_extract.v1.schema.json",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "input_context": {
            "title": "Example paper",
            "abstract_text": "Example abstract",
        },
    }
    job_path.write_text(json.dumps(job))

    response_packet = {
        "packet_type": "primary_paper_extract_v1",
        "schema_version": "v1",
        "source_document": {
            "source_type": "primary_paper",
            "title": "Example paper",
        },
        "entity_candidates": [],
        "claims": [],
        "validation_observations": [],
        "replication_signals": {},
        "unresolved_ambiguities": [],
    }

    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            return httpx.Response(500, json={"error": "temporary failure"})
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(response_packet)
                        }
                    }
                ]
            },
        )

    settings = get_settings().model_copy(
        update={
            "repo_root": tmp_path,
            "llm_api_key": "test-key",
            "llm_base_url": "https://example.test/v1",
            "llm_retry_attempts": 3,
            "llm_retry_base_delay_seconds": 0,
            "llm_retry_max_delay_seconds": 0,
        }
    )
    runner = LLMExtractionRunner(
        settings,
        client=httpx.Client(base_url=settings.llm_base_url, transport=httpx.MockTransport(handler)),
    )

    result = runner.run_job_file(job_path)
    runner.close()

    assert result["packet_type"] == "primary_paper_extract_v1"
    assert request_count == 2
