import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.load_plan import LoadPlanBuilder
from tool_db_backend.normalization import PacketNormalizer
from tool_db_backend.postgres_loader import PostgresLoadPlanExecutor


class _FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self._last_row = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        normalized = " ".join(query.split()).lower()
        params = params or ()

        if normalized.startswith("select id from source_document where doi = %s"):
            self._last_row = self.db.find_source_document_by("doi", params[0])
        elif normalized.startswith("select id from source_document where openalex_id = %s"):
            self._last_row = self.db.find_source_document_by("openalex_id", params[0])
        elif normalized.startswith("select id from source_document where semantic_scholar_id = %s"):
            self._last_row = self.db.find_source_document_by("semantic_scholar_id", params[0])
        elif normalized.startswith("select id from source_document where nct_id = %s"):
            self._last_row = self.db.find_source_document_by("nct_id", params[0])
        elif normalized.startswith("select id from source_document where title = %s"):
            self._last_row = self.db.find_source_document_by_title(*params)
        elif normalized.startswith("insert into source_document"):
            self._last_row = (self.db.insert_source_document(params),)
        elif normalized.startswith("select id from toolkit_item where slug = %s"):
            self._last_row = self.db.find_item_id(params[0])
        elif normalized.startswith("insert into toolkit_item"):
            self._last_row = (self.db.upsert_item(params),)
        elif normalized.startswith("insert into item_synonym"):
            self.db.insert_synonym(params)
            self._last_row = None
        elif normalized.startswith("insert into extracted_claim"):
            self._last_row = (self.db.insert_claim(params),)
        elif normalized.startswith("insert into claim_metric"):
            self.db.insert_claim_metric(params)
            self._last_row = None
        elif normalized.startswith("insert into claim_subject_link"):
            self.db.insert_claim_subject_link(params)
            self._last_row = None
        elif normalized.startswith("insert into item_citation"):
            self.db.insert_item_citation(params)
            self._last_row = None
        else:
            raise AssertionError(f"Unhandled query in fake cursor: {query}")

    def fetchone(self):
        return self._last_row


class FakeConnection:
    def __init__(self, db):
        self.db = db

    def transaction(self):
        return _FakeTransaction()

    def cursor(self):
        return FakeCursor(self.db)


class FakeDatabase:
    def __init__(self):
        self.source_documents = []
        self.items = {}
        self.synonyms = []
        self.claims = []
        self.claim_metrics = []
        self.claim_subject_links = []
        self.item_citations = []
        self._next_source_document_id = 1
        self._next_item_id = 1
        self._next_claim_id = 1

    def seed_item(self, slug):
        item_id = f"item-{self._next_item_id}"
        self._next_item_id += 1
        self.items[slug] = {"id": item_id, "slug": slug}
        return item_id

    def find_source_document_by(self, key, value):
        for row in self.source_documents:
            if row.get(key) == value:
                return (row["id"],)
        return None

    def find_source_document_by_title(self, title, publication_year, source_type):
        for row in self.source_documents:
            if row.get("title") == title and row.get("publication_year") == publication_year and row.get("source_type") == source_type:
                return (row["id"],)
        return None

    def insert_source_document(self, params):
        source_id = f"source-{self._next_source_document_id}"
        self._next_source_document_id += 1
        self.source_documents.append(
            {
                "id": source_id,
                "source_type": params[0],
                "title": params[1],
                "doi": params[2],
                "pmid": params[3],
                "openalex_id": params[4],
                "semantic_scholar_id": params[5],
                "nct_id": params[6],
                "publication_year": params[7],
                "journal_or_source": params[8],
            }
        )
        return source_id

    def find_item_id(self, slug):
        row = self.items.get(slug)
        return (row["id"],) if row else None

    def upsert_item(self, params):
        slug = params[0]
        existing = self.items.get(slug)
        if existing:
            return existing["id"]
        item_id = f"item-{self._next_item_id}"
        self._next_item_id += 1
        self.items[slug] = {"id": item_id, "slug": slug, "canonical_name": params[1], "item_type": params[2]}
        return item_id

    def insert_synonym(self, params):
        row = {"item_id": params[0], "synonym": params[1], "source_document_id": params[2]}
        if row not in self.synonyms:
            self.synonyms.append(row)

    def insert_claim(self, params):
        claim_id = f"claim-{self._next_claim_id}"
        self._next_claim_id += 1
        self.claims.append(
            {
                "id": claim_id,
                "source_document_id": params[0],
                "claim_type": params[1],
                "claim_text_normalized": params[2],
                "polarity": params[3],
            }
        )
        return claim_id

    def insert_claim_metric(self, params):
        self.claim_metrics.append({"claim_id": params[0], "metric_name": params[1]})

    def insert_claim_subject_link(self, params):
        self.claim_subject_links.append({"claim_id": params[0], "item_id": params[1], "subject_role": params[2]})

    def insert_item_citation(self, params):
        row = {"item_id": params[0], "source_document_id": params[1], "citation_role": params[2]}
        if row not in self.item_citations:
            self.item_citations.append(row)


def test_execute_load_plan_applies_existing_item_claims() -> None:
    settings = get_settings()
    payload = json.loads(Path("tests/fixtures/review_extract_v1.sample.json").read_text())
    normalized = PacketNormalizer(settings).normalize_packet("review_extract_v1", payload)
    load_plan = LoadPlanBuilder(settings).build_from_normalized_payload(normalized)

    fake_db = FakeDatabase()
    fake_db.seed_item("aslov2")
    fake_db.seed_item("cry2-cib1")
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(fake_db))

    result = executor.execute_load_plan(load_plan, apply=True)

    assert result["mode"] == "applied"
    assert result["inserted_claim_count"] == 2
    assert len(fake_db.claims) == 2
    assert len(fake_db.claim_subject_links) == 2
    assert len(fake_db.item_citations) == 2


def test_execute_load_plan_creates_new_candidate_item() -> None:
    settings = get_settings()
    load_plan = {
        "source_document": {"source_type": "review", "title": "New source"},
        "actions": {
            "toolkit_items": [
                {
                    "action": "create_item_candidate",
                    "local_id": "item_new_tool",
                    "proposed_slug": "new-tool",
                    "canonical_name": "New Tool",
                    "item_type": "protein_domain",
                    "aliases": ["Novel Tool"],
                    "external_ids": {},
                }
            ],
            "claims": [
                {
                    "action": "insert_extracted_claim",
                    "claim_local_id": "claim_1",
                    "claim_type": "mechanism_summary",
                    "claim_text_normalized": "New Tool is light-responsive.",
                    "polarity": "supports",
                    "subject_targets": [{"target_kind": "item_candidate", "proposed_slug": "new-tool"}],
                    "metrics": [],
                    "citation_role_suggestion": "best_review",
                }
            ],
        },
    }
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(FakeDatabase()))

    result = executor.execute_load_plan(load_plan, apply=True)

    assert result["mode"] == "applied"
    assert result["inserted_claim_count"] == 1


def test_execute_load_plan_dry_run_writes_review_queue(tmp_path: Path) -> None:
    settings = get_settings().model_copy(update={"repo_root": tmp_path})
    load_plan = {
        "source_document": {"source_type": "review", "title": "Ambiguous source"},
        "actions": {
            "toolkit_items": [
                {
                    "action": "manual_resolution_required",
                    "local_id": "item_x",
                    "candidate_matches": [{"slug": "aslov2", "matched_by": "slug"}],
                }
            ],
            "claims": [
                {
                    "action": "insert_extracted_claim",
                    "claim_local_id": "claim_x",
                    "claim_type": "mechanism_summary",
                    "claim_text_normalized": "Unresolved claim.",
                    "polarity": "supports",
                    "subject_targets": [],
                }
            ],
        },
    }
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(FakeDatabase()))
    review_path = tmp_path / "review-output.json"

    result = executor.execute_load_plan(load_plan, apply=False, review_output_path=review_path)

    assert result["mode"] == "dry_run"
    assert result["summary"]["review_task_count"] == 2
    payload = json.loads(review_path.read_text())
    assert payload["review_queue_type"] == "curation_review_queue_v1"
    assert len(payload["tasks"]) == 2
