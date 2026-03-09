from tool_db_backend.models import CanonicalClaim, SourceDocumentRecord, ValidationObservationRecord
from tool_db_backend.repository import KnowledgeRepository


def _source_document(
    source_id: str,
    title: str,
    *,
    source_type: str = "primary_paper",
    publication_year: int = 2024,
) -> SourceDocumentRecord:
    return SourceDocumentRecord(
        id=source_id,
        title=title,
        source_type=source_type,
        publication_year=publication_year,
        journal_or_source="Example Journal",
        doi="10.1000/example",
        pmid="12345678",
        is_retracted=False,
    )


def test_repository_derives_ranked_citations_from_claims_when_missing_item_citations() -> None:
    claims = [
        CanonicalClaim(
            id="claim-1",
            claim_type="application_result",
            claim_text_normalized="The tool controls transcription in yeast.",
            polarity="supports",
            needs_review=False,
            context={},
            source_locator={
                "quoted_text": "We demonstrate light-dependent control of transcription in yeast."
            },
            source_document=_source_document(
                "source-review",
                "Review of CBCR Tools",
                source_type="review",
                publication_year=2025,
            ),
            metrics=[],
        ),
        CanonicalClaim(
            id="claim-2",
            claim_type="engineering_result",
            claim_text_normalized="The tool binds biliverdin with high efficiency.",
            polarity="supports",
            needs_review=False,
            context={},
            source_locator={},
            source_document=_source_document(
                "source-primary",
                "Primary CBCR Paper",
                source_type="primary_paper",
                publication_year=2024,
            ),
            metrics=[],
        ),
    ]

    citations = KnowledgeRepository._derive_item_citations_from_evidence(  # noqa: SLF001
        claims,
        [],
    )

    assert len(citations) == 2
    assert citations[0]["citation_role"] == "best_review"
    assert citations[1]["citation_role"] == "foundational"
    assert citations[0]["importance_rank"] == 1
    assert "Derived from" in citations[0]["why_this_matters"]
    assert citations[0]["source_document_id"] == "source-review"
