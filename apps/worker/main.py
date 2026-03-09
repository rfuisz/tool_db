import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tool_db_backend.config import get_settings
from tool_db_backend.clients.clinicaltrials import ClinicalTrialsClient
from tool_db_backend.clients.europe_pmc import EuropePMCClient
from tool_db_backend.clients.gap_map import GapMapClient
from tool_db_backend.clients.openalex import OpenAlexClient
from tool_db_backend.clients.optobase import OptoBaseClient
from tool_db_backend.clients.pmc import PMCClient
from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.db_migrations import MigrationRunner
from tool_db_backend.first_pass_loader import FirstPassExtractionLoader
from tool_db_backend.gap_linking import GapLinkMaterializer
from tool_db_backend.item_materialization import ItemMaterializer
from tool_db_backend.llm_extractor import LLMExtractionError, LLMExtractionRunner
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer
from tool_db_backend.pipeline import PacketIngestPipeline
from tool_db_backend.pipeline import build_artifact_basename
from tool_db_backend.postgres_loader import PostgresLoadPlanExecutor
from tool_db_backend.raw_store import RawPayloadStore
from tool_db_backend.real_extraction_artifacts import RealExtractionArtifactBuilder
from tool_db_backend.seed_export import SeedExporter
from tool_db_backend.seed_loader import SeedLoader
from tool_db_backend.schema_validation import PACKET_TO_SCHEMA, PacketValidationError, validate_packet
from tool_db_backend.source_smoke_test import (
    RealDataHarvester,
    RealDataSmokeTester,
    build_first_pass_query_sets,
)
from tool_db_backend.source_staging import ClinicalTrialArtifactBuilder, OptoBaseSearchParser

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    settings = get_settings()
    level_name = str(settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def validate_packet_file(packet_kind: str, packet_path: str) -> int:
    payload = json.loads(Path(packet_path).read_text())
    try:
        validate_packet(packet_kind, payload, get_settings())
    except PacketValidationError as exc:
        print(f"invalid: {exc}")
        return 1

    print(f"valid: {packet_kind} -> {packet_path}")
    return 0


def export_seeds(output_dir: str) -> int:
    exporter = SeedExporter(get_settings())
    written_paths = exporter.write_split_files(Path(output_dir))
    for path in written_paths:
        print(f"wrote: {path}")
    return 0


def load_seed_bundle(bundle_path: str) -> int:
    loader = SeedLoader(get_settings())
    result = loader.load_bundle_file(Path(bundle_path))
    print(json.dumps({"bundle_path": bundle_path, **result}, indent=2))
    return 0


def _write_payload(
    source_key: str,
    resource_type: str,
    external_id: str,
    payload: dict,
    output_path: Optional[str] = None,
) -> int:
    rendered = json.dumps(payload, indent=2) + "\n"
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
        print(f"wrote: {path}")
        return 0

    path = RawPayloadStore(get_settings()).write_json_payload(
        source_key=source_key,
        resource_type=resource_type,
        external_id=external_id,
        payload=payload,
    )
    print(f"wrote: {path}")
    return 0


def fetch_openalex_work(work_id: str, output_path: Optional[str] = None) -> int:
    client = OpenAlexClient(get_settings())
    try:
        payload = client.fetch_work(work_id)
    finally:
        client.close()

    return _write_payload("openalex", "work", work_id, payload, output_path)


def fetch_europepmc_search(query: str, page_size: int = 25, page: int = 1, output_path: Optional[str] = None) -> int:
    client = EuropePMCClient(get_settings())
    try:
        payload = client.search(query=query, page_size=page_size, page=page, result_type="core")
    finally:
        client.close()

    return _write_payload("europe_pmc", "search", f"{query}-page-{page}", payload, output_path)


def fetch_pmc_fulltext(pmcid: str, output_path: Optional[str] = None) -> int:
    client = PMCClient(get_settings())
    try:
        payload = client.fetch_bioc_fulltext(pmcid)
    finally:
        client.close()

    return _write_payload("pmc", "bioc_fulltext", pmcid, payload, output_path)


def fetch_semantic_scholar_paper(
    paper_id: str,
    output_path: Optional[str] = None,
    fields: Optional[str] = None,
) -> int:
    client = SemanticScholarClient(get_settings())
    try:
        payload = client.fetch_paper(paper_id, fields=fields)
    finally:
        client.close()

    return _write_payload("semantic_scholar", "paper", paper_id, payload, output_path)


def fetch_clinicaltrials_study(nct_id: str, output_path: Optional[str] = None) -> int:
    client = ClinicalTrialsClient(get_settings())
    try:
        payload = client.fetch_study(nct_id)
    finally:
        client.close()

    return _write_payload("clinicaltrials_gov", "study", nct_id, payload, output_path)


def fetch_gapmap_dataset(dataset_name: str, output_path: Optional[str] = None) -> int:
    client = GapMapClient(get_settings())
    try:
        payload = client.fetch_dataset(dataset_name)
    finally:
        client.close()

    return _write_payload("gap_map", dataset_name, dataset_name, payload, output_path)


def fetch_optobase_search(query: str = "", output_path: Optional[str] = None) -> int:
    client = OptoBaseClient(get_settings())
    try:
        payload_text = client.fetch_search_page(query)
    finally:
        client.close()

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload_text)
        print(f"wrote: {path}")
        return 0

    path = RawPayloadStore(get_settings()).write_text_payload(
        source_key="optobase",
        resource_type="search_html",
        external_id=query or "search",
        payload_text=payload_text,
        content_type="text/html",
    )
    print(f"wrote: {path}")
    return 0


def build_clinicaltrials_packet(raw_path: str, output_path: str) -> int:
    builder = ClinicalTrialArtifactBuilder(get_settings())
    path = builder.build_packet_from_raw_file(Path(raw_path), Path(output_path))
    print(f"wrote: {path}")
    return 0


def parse_optobase_search_artifact(raw_path: str, output_path: str) -> int:
    parser = OptoBaseSearchParser()
    path = parser.write_summary_from_raw_file(Path(raw_path), Path(output_path))
    print(f"wrote: {path}")
    return 0


def _infer_packet_kind(packet_path: Path) -> str:
    payload = json.loads(packet_path.read_text())
    packet_kind = payload.get("packet_type")
    if packet_kind not in PACKET_TO_SCHEMA:
        raise ValueError(f"Unsupported or missing packet_type in {packet_path}: {packet_kind}")
    return packet_kind


def ingest_packet_batch(
    packet_dir: str,
    apply: bool = False,
    glob_pattern: str = "*.json",
    limit: Optional[int] = None,
    artifact_root: Optional[str] = None,
    review_output_dir: Optional[str] = None,
    manifest_path: Optional[str] = None,
) -> int:
    settings = get_settings()
    pipeline = PacketIngestPipeline(settings)
    packet_paths = sorted(Path(packet_dir).glob(glob_pattern))
    if limit is not None:
        packet_paths = packet_paths[:limit]

    completed = []
    failures = []
    for packet_path in packet_paths:
        try:
            packet_kind = _infer_packet_kind(packet_path)
            artifact_basename = build_artifact_basename(packet_path)
            per_packet_artifact_dir = (
                Path(artifact_root) / artifact_basename
                if artifact_root
                else settings.pipeline_artifact_root / artifact_basename
            )
            per_packet_review_output = (
                Path(review_output_dir) / f"{artifact_basename}.review.json"
                if review_output_dir
                else None
            )
            result = pipeline.ingest_packet_file(
                packet_kind=packet_kind,
                packet_path=packet_path,
                apply=apply,
                artifact_dir=per_packet_artifact_dir,
                review_output_path=per_packet_review_output,
            )
            completed.append(result)
        except (ValueError, PacketValidationError, RuntimeError) as exc:
            failures.append({"packet_path": str(packet_path), "error": str(exc)})

    report = {
        "packet_dir": str(Path(packet_dir)),
        "glob_pattern": glob_pattern,
        "selected_packet_count": len(packet_paths),
        "completed_packets": completed,
        "failed_packets": failures,
    }
    if manifest_path:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
        report["manifest_path"] = str(path)
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


def populate_local_db(
    literature_dir: str = "data/extractions",
    gap_dir: str = "data/pipeline-artifacts/real-extraction-seed/gap_map",
    review_output_dir: Optional[str] = None,
    manifest_path: Optional[str] = None,
) -> int:
    settings = get_settings()
    migration_runner = MigrationRunner(settings)
    seed_loader = SeedLoader(settings)
    first_pass_loader = FirstPassExtractionLoader(settings)
    materializer = ItemMaterializer(settings)

    applied_migrations = migration_runner.apply_all()
    seed_result = seed_loader.load_bundle_file(Path("db/seeds/knowledge_seed_bundle.v1.json"))

    literature_status = ingest_packet_batch(
        packet_dir=literature_dir,
        apply=True,
        artifact_root=str(settings.pipeline_artifact_root / "populate-local-db" / "literature"),
        review_output_dir=review_output_dir,
    )
    gap_status = ingest_packet_batch(
        packet_dir=gap_dir,
        apply=True,
        glob_pattern="*.database_entry_extract_v1.json",
        artifact_root=str(settings.pipeline_artifact_root / "populate-local-db" / "gap_map"),
        review_output_dir=review_output_dir,
    )
    first_pass_report = first_pass_loader.load_packet_batch(
        packet_dir=Path(literature_dir),
        glob_pattern="*.json",
        manifest_path=settings.pipeline_artifact_root / "populate-local-db" / "first-pass-report.json",
    )
    materialization_report = materializer.refresh()

    report = {
        "applied_migrations": applied_migrations,
        "seed_result": seed_result,
        "literature_status": literature_status,
        "gap_map_status": gap_status,
        "first_pass_selected_packet_count": first_pass_report["selected_packet_count"],
        "first_pass_failed_packet_count": len(first_pass_report["failed_packets"]),
        "materialization_report": materialization_report,
    }
    if manifest_path:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
        report["manifest_path"] = str(path)
    print(json.dumps(report, indent=2))
    return 0 if literature_status == 0 and gap_status == 0 and not first_pass_report["failed_packets"] else 1


def load_first_pass_extractions(
    packet_dir: str,
    glob_pattern: str = "*.json",
    limit: Optional[int] = None,
    manifest_path: Optional[str] = None,
) -> int:
    loader = FirstPassExtractionLoader(get_settings())
    report = loader.load_packet_batch(
        packet_dir=Path(packet_dir),
        glob_pattern=glob_pattern,
        limit=limit,
        manifest_path=Path(manifest_path) if manifest_path else None,
    )
    print(json.dumps(report, indent=2))
    return 0 if not report["failed_packets"] else 1


def normalize_packet_file(packet_kind: str, packet_path: str, output_path: str) -> int:
    normalizer = PacketNormalizer(get_settings())
    path = normalizer.write_normalized_packet(packet_kind, Path(packet_path), Path(output_path))
    print(f"wrote: {path}")
    return 0


def build_load_plan(normalized_path: str, output_path: str) -> int:
    builder = LoadPlanBuilder(get_settings())
    path = builder.write_load_plan(Path(normalized_path), Path(output_path))
    print(f"wrote: {path}")
    return 0


def execute_load_plan(
    load_plan_path: str,
    apply: bool = False,
    review_output_path: Optional[str] = None,
) -> int:
    executor = PostgresLoadPlanExecutor(get_settings())
    result = executor.execute_load_plan_file(
        Path(load_plan_path),
        apply=apply,
        review_output_path=Path(review_output_path) if review_output_path else None,
    )
    print(json.dumps(result, indent=2))
    return 0


def run_migrations() -> int:
    runner = MigrationRunner(get_settings())
    applied = runner.apply_all()
    print(json.dumps({"applied_migrations": applied}, indent=2))
    return 0


def materialize_item_details(item_slugs: Optional[List[str]] = None) -> int:
    materializer = ItemMaterializer(get_settings())
    result = materializer.refresh(item_slugs=item_slugs or None, include_related=True)
    print(json.dumps(result, indent=2))
    return 0


def materialize_gap_links(
    gap_slugs: Optional[List[str]] = None,
    item_slugs: Optional[List[str]] = None,
    include_item_types: Optional[List[str]] = None,
    exclude_item_types: Optional[List[str]] = None,
    max_candidates_per_gap: int = 12,
    max_links_per_gap: int = 6,
    refresh_item_details: bool = True,
) -> int:
    materializer = GapLinkMaterializer(get_settings())
    try:
        result = materializer.refresh(
            gap_slugs=gap_slugs or None,
            item_slugs=item_slugs or None,
            include_item_types=include_item_types or None,
            exclude_item_types=exclude_item_types or None,
            max_candidates_per_gap=max_candidates_per_gap,
            max_links_per_gap=max_links_per_gap,
            refresh_item_details=refresh_item_details,
        )
    finally:
        materializer.close()
    print(json.dumps(result, indent=2))
    return 0


def ingest_packet(
    packet_kind: str,
    packet_path: str,
    apply: bool = False,
    artifact_dir: Optional[str] = None,
    review_output_path: Optional[str] = None,
) -> int:
    settings = get_settings()
    pipeline = PacketIngestPipeline(settings)
    if artifact_dir:
        artifact_root = Path(artifact_dir)
    else:
        artifact_root = settings.pipeline_artifact_root / Path(packet_path).stem

    result = pipeline.ingest_packet_file(
        packet_kind=packet_kind,
        packet_path=Path(packet_path),
        apply=apply,
        artifact_dir=artifact_root,
        review_output_path=Path(review_output_path) if review_output_path else None,
    )
    print(json.dumps(result, indent=2))
    return 0


def smoke_test_real_data(artifact_dir: Optional[str] = None) -> int:
    settings = get_settings()
    tester = RealDataSmokeTester(settings)
    try:
        result = tester.run(Path(artifact_dir) if artifact_dir else None)
    finally:
        tester.close()
    print(json.dumps(result, indent=2))
    return 0


def harvest_real_data(
    artifact_dir: Optional[str] = None,
    profile: str = "broad",
    seed_query_limit: int = 24,
    europe_pmc_pages: int = 3,
    europe_pmc_page_size: int = 25,
    pmc_fulltext_limit: int = 50,
    openalex_pages: int = 3,
    openalex_per_page: int = 50,
    semantic_scholar_pages: int = 3,
    semantic_scholar_limit: int = 50,
    optobase_query_limit: int = 12,
) -> int:
    settings = get_settings()
    if profile == "smoke":
        tester = RealDataSmokeTester(settings)
        try:
            result = tester.run(Path(artifact_dir) if artifact_dir else None)
        finally:
            tester.close()
        print(json.dumps(result, indent=2))
        return 0

    query_sets = build_first_pass_query_sets(settings, seed_query_limit=seed_query_limit)
    harvester = RealDataHarvester(settings)
    try:
        result = harvester.run(
            artifact_dir=Path(artifact_dir) if artifact_dir else None,
            europe_pmc_queries=query_sets["europe_pmc"],
            europe_pmc_pages=europe_pmc_pages,
            europe_pmc_page_size=europe_pmc_page_size,
            pmc_fulltext_limit=pmc_fulltext_limit,
            openalex_queries=query_sets["openalex"],
            openalex_pages=openalex_pages,
            openalex_per_page=openalex_per_page,
            semantic_scholar_queries=query_sets["semantic_scholar"],
            semantic_scholar_pages=semantic_scholar_pages,
            semantic_scholar_limit=semantic_scholar_limit,
            optobase_queries=query_sets["optobase"][:optobase_query_limit],
        )
    finally:
        harvester.close()
    if query_sets.get("web_research"):
        result["query_expansion"] = query_sets["web_research"]
    print(json.dumps(result, indent=2))
    return 0


def build_real_extraction_artifacts(
    manifest_path: str,
    output_dir: str,
    gap_limit: int = 80,
    europe_pmc_limit: int = 200,
    openalex_limit: int = 200,
    semantic_scholar_limit: int = 200,
) -> int:
    builder = RealExtractionArtifactBuilder(get_settings())
    try:
        result = builder.build_from_smoke_test_manifest(
            manifest_path=Path(manifest_path),
            output_dir=Path(output_dir),
            gap_limit=gap_limit,
            europe_pmc_limit=europe_pmc_limit,
            openalex_limit=openalex_limit,
            semantic_scholar_limit=semantic_scholar_limit,
        )
    finally:
        builder.close()
    print(json.dumps(result, indent=2))
    return 0


def run_extraction_job(job_path: str, output_path: Optional[str] = None) -> int:
    runner = LLMExtractionRunner(get_settings())
    try:
        result = runner.run_job_file(Path(job_path), Path(output_path) if output_path else None)
    except LLMExtractionError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1
    finally:
        runner.close()

    print(json.dumps(result, indent=2))
    return 0


def _normalize_match_terms(values: Optional[List[str]]) -> List[str]:
    return [value.strip().lower() for value in (values or []) if value.strip()]


def _job_matches_terms(job_path: Path, include_terms: List[str], exclude_terms: List[str]) -> bool:
    haystacks = [job_path.stem.lower()]
    try:
        payload = json.loads(job_path.read_text())
        source_document = payload.get("source_document", {})
        input_context = payload.get("input_context", {})
        haystacks.extend(
            [
                str(source_document.get("title", "")).lower(),
                str(input_context.get("title", "")).lower(),
                str(input_context.get("abstract_text", "")).lower(),
            ]
        )
    except (json.JSONDecodeError, OSError):
        pass

    searchable = "\n".join(haystacks)
    if include_terms and not any(term in searchable for term in include_terms):
        return False
    if exclude_terms and any(term in searchable for term in exclude_terms):
        return False
    return True


def _existing_extraction_outputs(settings, job_path: Path) -> List[Path]:
    pattern = re.escape(job_path.stem).replace("\\*", "*")
    return sorted(settings.extraction_root.glob(f"{job_path.stem}.*.json"))


def _run_extraction_job_path(settings, job_path: Path) -> Dict[str, str]:
    runner = LLMExtractionRunner(settings)
    try:
        return runner.run_job_file(job_path)
    finally:
        runner.close()


def run_extraction_batch(
    job_dir: str,
    limit: Optional[int] = 50,
    include_terms: Optional[List[str]] = None,
    exclude_terms: Optional[List[str]] = None,
    skip_existing: bool = True,
    manifest_path: Optional[str] = None,
    max_workers: Optional[int] = None,
) -> int:
    settings = get_settings()
    effective_max_workers = max_workers if max_workers is not None else settings.llm_max_concurrency
    results = []
    failures = []
    skipped_existing = []
    skipped_filtered_out = []
    include_terms_normalized = _normalize_match_terms(include_terms)
    exclude_terms_normalized = _normalize_match_terms(exclude_terms)
    all_job_paths = sorted(Path(job_dir).glob("*.json"))
    selected_job_paths: List[Path] = []

    for job_path in all_job_paths:
        if not _job_matches_terms(job_path, include_terms_normalized, exclude_terms_normalized):
            skipped_filtered_out.append(str(job_path))
            continue
        existing_outputs = _existing_extraction_outputs(settings, job_path)
        if skip_existing and existing_outputs:
            skipped_existing.append(
                {
                    "job_path": str(job_path),
                    "existing_outputs": [str(path) for path in existing_outputs],
                }
            )
            continue
        selected_job_paths.append(job_path)
        if limit is not None and limit > 0 and len(selected_job_paths) >= limit:
            break

    if effective_max_workers <= 1:
        for job_path in selected_job_paths:
            try:
                results.append(_run_extraction_job_path(settings, job_path))
            except (LLMExtractionError, OSError, ValueError) as exc:
                failures.append({"job_path": str(job_path), "error": str(exc)})
    else:
        with ThreadPoolExecutor(max_workers=effective_max_workers) as executor:
            futures = {
                executor.submit(_run_extraction_job_path, settings, job_path): job_path
                for job_path in selected_job_paths
            }
            for future in as_completed(futures):
                job_path = futures[future]
                try:
                    results.append(future.result())
                except (LLMExtractionError, OSError, ValueError) as exc:
                    failures.append({"job_path": str(job_path), "error": str(exc)})

    report = {
        "job_dir": str(Path(job_dir)),
        "selected_job_count": len(selected_job_paths),
        "limit": limit,
        "max_workers": effective_max_workers,
        "completed_jobs": results,
        "failed_jobs": failures,
        "skipped_existing": skipped_existing,
        "skipped_filtered_out_count": len(skipped_filtered_out),
        "include_terms": include_terms_normalized,
        "exclude_terms": exclude_terms_normalized,
    }
    if manifest_path:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")
        report["manifest_path"] = str(path)

    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


def main(argv: Optional[List[str]] = None) -> int:
    args = argv or sys.argv[1:]
    configure_logging()
    if len(args) == 2 and args[0] in PACKET_TO_SCHEMA:
        packet_kind, packet_path = args
        return validate_packet_file(packet_kind, packet_path)

    parser = argparse.ArgumentParser(description="Worker utilities for the BioControl Toolkit DB.")
    subparsers = parser.add_subparsers(dest="command")

    validate_parser = subparsers.add_parser("validate-packet", help="Validate an extraction packet JSON file.")
    validate_parser.add_argument("packet_kind")
    validate_parser.add_argument("packet_path")

    export_parser = subparsers.add_parser("export-seeds", help="Export JSON seed artifacts from repo knowledge files.")
    export_parser.add_argument("output_dir")

    load_seed_parser = subparsers.add_parser(
        "load-seed-bundle",
        help="Load seed items and workflows into Postgres.",
    )
    load_seed_parser.add_argument(
        "bundle_path",
        nargs="?",
        default="db/seeds/knowledge_seed_bundle.v1.json",
    )

    openalex_parser = subparsers.add_parser("fetch-openalex-work", help="Fetch an OpenAlex work payload.")
    openalex_parser.add_argument("work_id")
    openalex_parser.add_argument("--output-path")

    europepmc_parser = subparsers.add_parser(
        "fetch-europepmc-search",
        help="Fetch a Europe PMC search payload.",
    )
    europepmc_parser.add_argument("query")
    europepmc_parser.add_argument("--page-size", type=int, default=25)
    europepmc_parser.add_argument("--page", type=int, default=1)
    europepmc_parser.add_argument("--output-path")

    pmc_parser = subparsers.add_parser(
        "fetch-pmc-fulltext",
        help="Fetch a PMC BioC full-text payload.",
    )
    pmc_parser.add_argument("pmcid")
    pmc_parser.add_argument("--output-path")

    semantic_scholar_parser = subparsers.add_parser(
        "fetch-semanticscholar-paper",
        help="Fetch a Semantic Scholar paper payload.",
    )
    semantic_scholar_parser.add_argument("paper_id")
    semantic_scholar_parser.add_argument("--fields")
    semantic_scholar_parser.add_argument("--output-path")

    clinicaltrials_parser = subparsers.add_parser(
        "fetch-clinicaltrials-study",
        help="Fetch a ClinicalTrials.gov study payload.",
    )
    clinicaltrials_parser.add_argument("nct_id")
    clinicaltrials_parser.add_argument("--output-path")

    gapmap_parser = subparsers.add_parser(
        "fetch-gapmap-dataset",
        help="Fetch a Gap Map dataset JSON payload.",
    )
    gapmap_parser.add_argument("dataset_name")
    gapmap_parser.add_argument("--output-path")

    optobase_parser = subparsers.add_parser(
        "fetch-optobase-search",
        help="Fetch an OptoBase search HTML page.",
    )
    optobase_parser.add_argument("--query", default="")
    optobase_parser.add_argument("--output-path")

    clinicaltrials_packet_parser = subparsers.add_parser(
        "build-clinicaltrials-packet",
        help="Build a deterministic trial_extract_v1 packet from a raw ClinicalTrials.gov payload wrapper.",
    )
    clinicaltrials_packet_parser.add_argument("raw_path")
    clinicaltrials_packet_parser.add_argument("output_path")

    optobase_parse_parser = subparsers.add_parser(
        "parse-optobase-search",
        help="Parse a raw OptoBase HTML payload wrapper into a structured summary artifact.",
    )
    optobase_parse_parser.add_argument("raw_path")
    optobase_parse_parser.add_argument("output_path")

    normalize_parser = subparsers.add_parser(
        "normalize-packet",
        help="Normalize a validated extraction packet into merge-ready JSON.",
    )
    normalize_parser.add_argument("packet_kind")
    normalize_parser.add_argument("packet_path")
    normalize_parser.add_argument("output_path")

    load_plan_parser = subparsers.add_parser(
        "build-load-plan",
        help="Build a conservative canonical load plan from a normalized packet.",
    )
    load_plan_parser.add_argument("normalized_path")
    load_plan_parser.add_argument("output_path")

    execute_parser = subparsers.add_parser(
        "execute-load-plan",
        help="Dry-run or apply a load plan to Postgres with review queue output.",
    )
    execute_parser.add_argument("load_plan_path")
    execute_parser.add_argument("--apply", action="store_true")
    execute_parser.add_argument("--review-output-path")

    migrate_parser = subparsers.add_parser(
        "run-migrations",
        help="Apply SQL migrations to the configured Postgres database.",
    )

    materialize_parser = subparsers.add_parser(
        "materialize-item-details",
        help="Recompute canonical item facets, explainers, comparisons, and scores.",
    )
    materialize_parser.add_argument("item_slugs", nargs="*")

    gap_link_parser = subparsers.add_parser(
        "materialize-gap-links",
        help="Use GPT to map eligible collection items onto Gap Map problems and store ranked links.",
    )
    gap_link_parser.add_argument("--gap-slug", action="append", default=[])
    gap_link_parser.add_argument("--item-slug", action="append", default=[])
    gap_link_parser.add_argument("--include-item-type", action="append", default=[])
    gap_link_parser.add_argument("--exclude-item-type", action="append", default=[])
    gap_link_parser.add_argument("--max-candidates-per-gap", type=int, default=12)
    gap_link_parser.add_argument("--max-links-per-gap", type=int, default=6)
    gap_link_parser.add_argument(
        "--no-refresh-item-details",
        action="store_false",
        dest="refresh_item_details",
        help="Skip the follow-on item detail materialization pass.",
    )
    gap_link_parser.set_defaults(refresh_item_details=True)

    ingest_parser = subparsers.add_parser(
        "ingest-packet",
        help="Run validate -> normalize -> load-plan -> execute for an extraction packet.",
    )
    ingest_parser.add_argument("packet_kind")
    ingest_parser.add_argument("packet_path")
    ingest_parser.add_argument("--apply", action="store_true")
    ingest_parser.add_argument("--artifact-dir")
    ingest_parser.add_argument("--review-output-path")

    ingest_batch_parser = subparsers.add_parser(
        "ingest-packet-batch",
        help="Run the packet ingest pipeline over a directory of packet JSON files.",
    )
    ingest_batch_parser.add_argument("packet_dir")
    ingest_batch_parser.add_argument("--apply", action="store_true")
    ingest_batch_parser.add_argument("--glob-pattern", default="*.json")
    ingest_batch_parser.add_argument("--limit", type=int)
    ingest_batch_parser.add_argument("--artifact-root")
    ingest_batch_parser.add_argument("--review-output-dir")
    ingest_batch_parser.add_argument("--manifest-path")

    populate_parser = subparsers.add_parser(
        "populate-local-db",
        help="Run migrations, load seed knowledge, and ingest checked-in literature and gap-map packets.",
    )
    populate_parser.add_argument("--literature-dir", default="data/extractions")
    populate_parser.add_argument("--gap-dir", default="data/pipeline-artifacts/real-extraction-seed/gap_map")
    populate_parser.add_argument("--review-output-dir")
    populate_parser.add_argument("--manifest-path")

    first_pass_parser = subparsers.add_parser(
        "load-first-pass-extractions",
        help="Load extracted packets into permissive first-pass review tables for bulk inspection.",
    )
    first_pass_parser.add_argument("packet_dir")
    first_pass_parser.add_argument("--glob-pattern", default="*.json")
    first_pass_parser.add_argument("--limit", type=int)
    first_pass_parser.add_argument("--manifest-path")

    smoke_test_parser = subparsers.add_parser(
        "smoke-test-real-data",
        help="Fetch a modest batch of real literature and gap/problem data.",
    )
    smoke_test_parser.add_argument("--artifact-dir")

    harvest_parser = subparsers.add_parser(
        "harvest-real-data",
        help="Fetch a broader first-pass literature/problem corpus using seed- and vocabulary-expanded queries.",
    )
    harvest_parser.add_argument("--artifact-dir")
    harvest_parser.add_argument("--profile", choices=["smoke", "broad"], default="broad")
    harvest_parser.add_argument("--seed-query-limit", type=int, default=24)
    harvest_parser.add_argument("--europe-pmc-pages", type=int, default=3)
    harvest_parser.add_argument("--europe-pmc-page-size", type=int, default=25)
    harvest_parser.add_argument("--pmc-fulltext-limit", type=int, default=50)
    harvest_parser.add_argument("--openalex-pages", type=int, default=3)
    harvest_parser.add_argument("--openalex-per-page", type=int, default=50)
    harvest_parser.add_argument("--semantic-scholar-pages", type=int, default=3)
    harvest_parser.add_argument("--semantic-scholar-limit", type=int, default=50)
    harvest_parser.add_argument("--optobase-query-limit", type=int, default=12)

    extraction_artifacts_parser = subparsers.add_parser(
        "build-real-extraction-artifacts",
        help="Turn fetched real data into typed extraction packets and LLM job artifacts.",
    )
    extraction_artifacts_parser.add_argument("manifest_path")
    extraction_artifacts_parser.add_argument("output_dir")
    extraction_artifacts_parser.add_argument("--gap-limit", type=int, default=80)
    extraction_artifacts_parser.add_argument("--europe-pmc-limit", type=int, default=200)
    extraction_artifacts_parser.add_argument("--openalex-limit", type=int, default=200)
    extraction_artifacts_parser.add_argument("--semantic-scholar-limit", type=int, default=200)

    extraction_job_parser = subparsers.add_parser(
        "run-extraction-job",
        help="Run one LLM extraction job and validate the output packet.",
    )
    extraction_job_parser.add_argument("job_path")
    extraction_job_parser.add_argument("--output-path")

    extraction_batch_parser = subparsers.add_parser(
        "run-extraction-batch",
        help="Run a larger batch of LLM extraction jobs.",
    )
    extraction_batch_parser.add_argument("job_dir")
    extraction_batch_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum jobs to run; pass 0 to run all eligible jobs.",
    )
    extraction_batch_parser.add_argument(
        "--max-workers",
        type=int,
        help="Concurrent extraction workers to run. Defaults to LLM_MAX_CONCURRENCY.",
    )
    extraction_batch_parser.add_argument(
        "--include-term",
        action="append",
        default=[],
        help="Case-insensitive term that must appear in the job title, abstract, or filename.",
    )
    extraction_batch_parser.add_argument(
        "--exclude-term",
        action="append",
        default=[],
        help="Case-insensitive term that excludes a job when found in the title, abstract, or filename.",
    )
    extraction_batch_parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Re-run jobs even if extraction outputs already exist.",
    )
    extraction_batch_parser.set_defaults(skip_existing=True)
    extraction_batch_parser.add_argument("--manifest-path")

    parsed = parser.parse_args(args)

    if parsed.command == "validate-packet":
        return validate_packet_file(parsed.packet_kind, parsed.packet_path)
    if parsed.command == "export-seeds":
        return export_seeds(parsed.output_dir)
    if parsed.command == "load-seed-bundle":
        return load_seed_bundle(parsed.bundle_path)
    if parsed.command == "fetch-openalex-work":
        return fetch_openalex_work(parsed.work_id, parsed.output_path)
    if parsed.command == "fetch-europepmc-search":
        return fetch_europepmc_search(parsed.query, parsed.page_size, parsed.page, parsed.output_path)
    if parsed.command == "fetch-pmc-fulltext":
        return fetch_pmc_fulltext(parsed.pmcid, parsed.output_path)
    if parsed.command == "fetch-semanticscholar-paper":
        return fetch_semantic_scholar_paper(parsed.paper_id, parsed.output_path, parsed.fields)
    if parsed.command == "fetch-clinicaltrials-study":
        return fetch_clinicaltrials_study(parsed.nct_id, parsed.output_path)
    if parsed.command == "fetch-gapmap-dataset":
        return fetch_gapmap_dataset(parsed.dataset_name, parsed.output_path)
    if parsed.command == "fetch-optobase-search":
        return fetch_optobase_search(parsed.query, parsed.output_path)
    if parsed.command == "build-clinicaltrials-packet":
        return build_clinicaltrials_packet(parsed.raw_path, parsed.output_path)
    if parsed.command == "parse-optobase-search":
        return parse_optobase_search_artifact(parsed.raw_path, parsed.output_path)
    if parsed.command == "normalize-packet":
        return normalize_packet_file(parsed.packet_kind, parsed.packet_path, parsed.output_path)
    if parsed.command == "build-load-plan":
        return build_load_plan(parsed.normalized_path, parsed.output_path)
    if parsed.command == "execute-load-plan":
        return execute_load_plan(parsed.load_plan_path, parsed.apply, parsed.review_output_path)
    if parsed.command == "run-migrations":
        return run_migrations()
    if parsed.command == "materialize-item-details":
        return materialize_item_details(parsed.item_slugs)
    if parsed.command == "materialize-gap-links":
        return materialize_gap_links(
            gap_slugs=parsed.gap_slug,
            item_slugs=parsed.item_slug,
            include_item_types=parsed.include_item_type,
            exclude_item_types=parsed.exclude_item_type,
            max_candidates_per_gap=parsed.max_candidates_per_gap,
            max_links_per_gap=parsed.max_links_per_gap,
            refresh_item_details=parsed.refresh_item_details,
        )
    if parsed.command == "ingest-packet":
        return ingest_packet(
            parsed.packet_kind,
            parsed.packet_path,
            parsed.apply,
            parsed.artifact_dir,
            parsed.review_output_path,
        )
    if parsed.command == "ingest-packet-batch":
        return ingest_packet_batch(
            parsed.packet_dir,
            parsed.apply,
            parsed.glob_pattern,
            parsed.limit,
            parsed.artifact_root,
            parsed.review_output_dir,
            parsed.manifest_path,
        )
    if parsed.command == "populate-local-db":
        return populate_local_db(
            parsed.literature_dir,
            parsed.gap_dir,
            parsed.review_output_dir,
            parsed.manifest_path,
        )
    if parsed.command == "load-first-pass-extractions":
        return load_first_pass_extractions(
            parsed.packet_dir,
            parsed.glob_pattern,
            parsed.limit,
            parsed.manifest_path,
        )
    if parsed.command == "smoke-test-real-data":
        return smoke_test_real_data(parsed.artifact_dir)
    if parsed.command == "harvest-real-data":
        return harvest_real_data(
            parsed.artifact_dir,
            parsed.profile,
            parsed.seed_query_limit,
            parsed.europe_pmc_pages,
            parsed.europe_pmc_page_size,
            parsed.pmc_fulltext_limit,
            parsed.openalex_pages,
            parsed.openalex_per_page,
            parsed.semantic_scholar_pages,
            parsed.semantic_scholar_limit,
            parsed.optobase_query_limit,
        )
    if parsed.command == "build-real-extraction-artifacts":
        return build_real_extraction_artifacts(
            parsed.manifest_path,
            parsed.output_dir,
            parsed.gap_limit,
            parsed.europe_pmc_limit,
            parsed.openalex_limit,
            parsed.semantic_scholar_limit,
        )
    if parsed.command == "run-extraction-job":
        return run_extraction_job(parsed.job_path, parsed.output_path)
    if parsed.command == "run-extraction-batch":
        return run_extraction_batch(
            parsed.job_dir,
            parsed.limit,
            parsed.include_term,
            parsed.exclude_term,
            parsed.skip_existing,
            parsed.manifest_path,
            parsed.max_workers,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
