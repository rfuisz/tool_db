import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tool_db_backend.config import get_settings
from tool_db_backend.clients.clinicaltrials import ClinicalTrialsClient
from tool_db_backend.clients.gap_map import GapMapClient
from tool_db_backend.clients.openalex import OpenAlexClient
from tool_db_backend.clients.optobase import OptoBaseClient
from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.db_migrations import MigrationRunner
from tool_db_backend.llm_extractor import LLMExtractionError, LLMExtractionRunner
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer
from tool_db_backend.pipeline import PacketIngestPipeline
from tool_db_backend.postgres_loader import PostgresLoadPlanExecutor
from tool_db_backend.raw_store import RawPayloadStore
from tool_db_backend.real_extraction_artifacts import RealExtractionArtifactBuilder
from tool_db_backend.seed_export import SeedExporter
from tool_db_backend.seed_loader import SeedLoader
from tool_db_backend.schema_validation import PACKET_TO_SCHEMA, PacketValidationError, validate_packet
from tool_db_backend.source_smoke_test import RealDataSmokeTester


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


def build_real_extraction_artifacts(
    manifest_path: str,
    output_dir: str,
    gap_limit: int = 80,
    openalex_limit: int = 40,
) -> int:
    builder = RealExtractionArtifactBuilder(get_settings())
    try:
        result = builder.build_from_smoke_test_manifest(
            manifest_path=Path(manifest_path),
            output_dir=Path(output_dir),
            gap_limit=gap_limit,
            openalex_limit=openalex_limit,
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


def run_extraction_batch(job_dir: str, limit: int = 3) -> int:
    runner = LLMExtractionRunner(get_settings())
    results = []
    failures = []
    job_paths = sorted(Path(job_dir).glob("*.json"))[:limit]
    try:
        for job_path in job_paths:
            try:
                results.append(runner.run_job_file(job_path))
            except LLMExtractionError as exc:
                failures.append({"job_path": str(job_path), "error": str(exc)})
    finally:
        runner.close()

    print(json.dumps({"completed_jobs": results, "failed_jobs": failures}, indent=2))
    return 0 if not failures else 1


def main(argv: Optional[List[str]] = None) -> int:
    args = argv or sys.argv[1:]
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

    ingest_parser = subparsers.add_parser(
        "ingest-packet",
        help="Run validate -> normalize -> load-plan -> execute for an extraction packet.",
    )
    ingest_parser.add_argument("packet_kind")
    ingest_parser.add_argument("packet_path")
    ingest_parser.add_argument("--apply", action="store_true")
    ingest_parser.add_argument("--artifact-dir")
    ingest_parser.add_argument("--review-output-path")

    smoke_test_parser = subparsers.add_parser(
        "smoke-test-real-data",
        help="Fetch a modest batch of real literature and gap/problem data.",
    )
    smoke_test_parser.add_argument("--artifact-dir")

    extraction_artifacts_parser = subparsers.add_parser(
        "build-real-extraction-artifacts",
        help="Turn fetched real data into typed extraction packets and LLM job artifacts.",
    )
    extraction_artifacts_parser.add_argument("manifest_path")
    extraction_artifacts_parser.add_argument("output_dir")
    extraction_artifacts_parser.add_argument("--gap-limit", type=int, default=80)
    extraction_artifacts_parser.add_argument("--openalex-limit", type=int, default=40)

    extraction_job_parser = subparsers.add_parser(
        "run-extraction-job",
        help="Run one LLM extraction job and validate the output packet.",
    )
    extraction_job_parser.add_argument("job_path")
    extraction_job_parser.add_argument("--output-path")

    extraction_batch_parser = subparsers.add_parser(
        "run-extraction-batch",
        help="Run a small batch of LLM extraction jobs.",
    )
    extraction_batch_parser.add_argument("job_dir")
    extraction_batch_parser.add_argument("--limit", type=int, default=3)

    parsed = parser.parse_args(args)

    if parsed.command == "validate-packet":
        return validate_packet_file(parsed.packet_kind, parsed.packet_path)
    if parsed.command == "export-seeds":
        return export_seeds(parsed.output_dir)
    if parsed.command == "load-seed-bundle":
        return load_seed_bundle(parsed.bundle_path)
    if parsed.command == "fetch-openalex-work":
        return fetch_openalex_work(parsed.work_id, parsed.output_path)
    if parsed.command == "fetch-semanticscholar-paper":
        return fetch_semantic_scholar_paper(parsed.paper_id, parsed.output_path, parsed.fields)
    if parsed.command == "fetch-clinicaltrials-study":
        return fetch_clinicaltrials_study(parsed.nct_id, parsed.output_path)
    if parsed.command == "fetch-gapmap-dataset":
        return fetch_gapmap_dataset(parsed.dataset_name, parsed.output_path)
    if parsed.command == "fetch-optobase-search":
        return fetch_optobase_search(parsed.query, parsed.output_path)
    if parsed.command == "normalize-packet":
        return normalize_packet_file(parsed.packet_kind, parsed.packet_path, parsed.output_path)
    if parsed.command == "build-load-plan":
        return build_load_plan(parsed.normalized_path, parsed.output_path)
    if parsed.command == "execute-load-plan":
        return execute_load_plan(parsed.load_plan_path, parsed.apply, parsed.review_output_path)
    if parsed.command == "run-migrations":
        return run_migrations()
    if parsed.command == "ingest-packet":
        return ingest_packet(
            parsed.packet_kind,
            parsed.packet_path,
            parsed.apply,
            parsed.artifact_dir,
            parsed.review_output_path,
        )
    if parsed.command == "smoke-test-real-data":
        return smoke_test_real_data(parsed.artifact_dir)
    if parsed.command == "build-real-extraction-artifacts":
        return build_real_extraction_artifacts(
            parsed.manifest_path,
            parsed.output_dir,
            parsed.gap_limit,
            parsed.openalex_limit,
        )
    if parsed.command == "run-extraction-job":
        return run_extraction_job(parsed.job_path, parsed.output_path)
    if parsed.command == "run-extraction-batch":
        return run_extraction_batch(parsed.job_dir, parsed.limit)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
