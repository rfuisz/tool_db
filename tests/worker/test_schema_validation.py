import json
from pathlib import Path

import pytest

from tool_db_backend.config import get_settings
from tool_db_backend.schema_validation import PacketValidationError, validate_packet


def test_review_fixture_validates() -> None:
    fixture_path = Path("tests/fixtures/review_extract_v1.sample.json")
    payload = json.loads(fixture_path.read_text())

    validate_packet("review_extract_v1", payload, get_settings())


def test_invalid_review_fixture_fails_validation() -> None:
    payload = {
        "packet_type": "review_extract_v1",
        "schema_version": "v1",
        "source_document": {
            "source_type": "review",
            "title": "broken fixture"
        },
        "entity_candidates": [],
        "workflow_stage_observations": [],
        "claims": [
            {
                "local_id": "claim_1",
                "claim_type": "mechanism_summary",
                "claim_text_normalized": "Broken because subject IDs are missing.",
                "polarity": "supports"
            }
        ],
        "unresolved_ambiguities": []
    }

    with pytest.raises(PacketValidationError):
        validate_packet("review_extract_v1", payload, get_settings())
