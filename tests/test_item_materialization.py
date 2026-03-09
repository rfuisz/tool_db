from tool_db_backend.config import get_settings
from tool_db_backend.item_materialization import (
    ExtractedItemEvidence,
    ItemContext,
    ItemMaterializer,
)


def _source_document(source_id: str, title: str) -> dict:
    return {
        "id": source_id,
        "title": title,
        "source_type": "primary_paper",
        "publication_year": 2024,
        "journal_or_source": "Example Journal",
        "doi": "10.1000/example",
        "pmid": "12345678",
        "is_retracted": False,
    }


def _empty_context(name: str, slug: str) -> ItemContext:
    return ItemContext(
        item_id=slug,
        slug=slug,
        canonical_name=name,
        item_type="multi_component_switch",
        summary=None,
        primary_input_modality="light",
        primary_output_modality="transcription",
        mechanisms=["heterodimerization"],
        techniques=[],
        target_processes=["transcription"],
        synonyms=[],
        claims=[],
        validations=[],
        citations=[],
        gap_links=[],
        extracted_evidence=[],
    )


def test_item_materializer_prefers_literature_backed_explainers() -> None:
    materializer = ItemMaterializer(get_settings())
    context = _empty_context("ExampleSwitch", "example-switch")
    context.extracted_evidence = [
        ExtractedItemEvidence(
            local_id="item_1",
            source_document=_source_document("source-1", "Example Paper"),
            evidence_text="The abstract describes a light-gated transcription switch.",
            useful_for=["temporal control of transcription"],
            problem_solved=["reduce constitutive transcriptional activation"],
            strengths=["works without an added cofactor"],
            limitations=["context-specific leakage is still reported"],
            implementation_constraints=["requires blue-light illumination"],
            freeform_explainers={
                "what_it_does": "Enables light-gated recruitment of transcriptional effectors.",
                "resources_required": "Requires blue-light illumination and compatible fusion constructs.",
                "problem_it_solves": "Provides temporal control over transcription without constitutive recruitment.",
                "problem_it_does_not_solve": "Does not by itself solve downstream delivery constraints.",
                "alternatives": "The paper contrasts this switch with PhyB/PIF when different spectral properties are needed.",
            },
        )
    ]
    replication_summary = {
        "independent_primary_paper_count": 0,
        "distinct_biological_contexts": 0,
        "practicality_penalties": [],
        "orphan_tool_flag": False,
    }

    problem_links = materializer._derive_problem_links(context)  # noqa: SLF001
    explainers = materializer._derive_explainers(  # noqa: SLF001
        context,
        replication_summary=replication_summary,
        facets=[],
        problem_links=problem_links,
    )
    explainers_by_kind = {explainer["explainer_kind"]: explainer for explainer in explainers}

    assert explainers_by_kind["usefulness"]["body"] == (
        "Enables light-gated recruitment of transcriptional effectors.; temporal control of transcription"
    )
    assert explainers_by_kind["alternatives"]["evidence_payload"]["source_kind"] == "literature_extract"
    assert problem_links[0]["source_kind"] == "literature_extract"


def test_item_materializer_builds_literature_backed_comparisons_before_heuristics() -> None:
    materializer = ItemMaterializer(get_settings())
    context = _empty_context("ExampleSwitch", "example-switch")
    context.synonyms = ["Example Switch"]
    context.extracted_evidence = [
        ExtractedItemEvidence(
            local_id="item_1",
            source_document=_source_document("source-1", "Example Paper"),
            evidence_text="The source explicitly compares ExampleSwitch against PhyB/PIF.",
            useful_for=[],
            problem_solved=[],
            strengths=["simpler cofactor requirements"],
            limitations=["blue-light penetration remains limited"],
            implementation_constraints=[],
            freeform_explainers={
                "alternatives": "Compared with PhyB/PIF, ExampleSwitch is easier to run when exogenous chromophore handling is undesirable."
            },
        )
    ]
    candidate = _empty_context("PhyB/PIF", "phyb-pif")
    candidate.synonyms = ["PhyB PIF"]

    comparisons = materializer._build_literature_comparisons(  # noqa: SLF001
        context,
        [context, candidate],
    )

    assert len(comparisons) == 1
    assert comparisons[0]["related_item_id"] == "phyb-pif"
    assert comparisons[0]["relation_type"] == "source_stated_alternative"
    assert comparisons[0]["evidence_payload"]["source_kind"] == "literature_extract"


def test_item_materializer_uses_claims_when_no_literature_explainers_exist() -> None:
    materializer = ItemMaterializer(get_settings())
    context = _empty_context("Am1_c0023g2", "am1-c0023g2")
    context.claims = [
        {
            "id": "claim-1",
            "claim_type": "application_result",
            "claim_text_normalized": "Am1_c0023g2 enables light-dependent control of transcription in yeast.",
            "source_locator": {
                "quoted_text": "We demonstrate light-dependent control of transcription in yeast using Am1_c0023g2-derived tools."
            },
            "source_document": _source_document("source-1", "CBCR Tools Paper"),
        },
        {
            "id": "claim-2",
            "claim_type": "engineering_result",
            "claim_text_normalized": "Am1_c0023g2 binders were developed for different photostates under PCB and biliverdin conditions.",
            "source_locator": {
                "quoted_text": "We developed monomeric binders selective for different Am1_c0023g2 photostates under PCB and biliverdin conditions."
            },
            "source_document": _source_document("source-2", "Binder Engineering Paper"),
        },
    ]
    replication_summary = {
        "independent_primary_paper_count": 0,
        "distinct_biological_contexts": 0,
        "practicality_penalties": [],
        "orphan_tool_flag": False,
    }

    explainers = materializer._derive_explainers(  # noqa: SLF001
        context,
        replication_summary=replication_summary,
        facets=[],
        problem_links=[],
    )
    explainers_by_kind = {explainer["explainer_kind"]: explainer for explainer in explainers}

    assert explainers_by_kind["usefulness"]["evidence_payload"]["source_kind"] == "canonical_claim"
    assert "light-dependent control of transcription in yeast" in explainers_by_kind["usefulness"]["body"]
    assert explainers_by_kind["implementation_constraints"]["evidence_payload"]["source_kind"] == "canonical_claim"
