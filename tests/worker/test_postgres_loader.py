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
        elif normalized.startswith("select item_type::text from toolkit_item where id = %s"):
            self._last_row = self.db.find_item_type(params[0])
        elif normalized.startswith("select summary, primary_input_modality::text, primary_output_modality::text from toolkit_item where id = %s"):
            self._last_row = self.db.find_item_details(params[0])
        elif normalized.startswith("insert into toolkit_item"):
            self._last_row = (self.db.upsert_item(params),)
        elif normalized.startswith("update toolkit_item set item_type = %s::item_type"):
            self.db.update_item_type(params)
            self._last_row = None
        elif normalized.startswith("update toolkit_item set summary = %s, primary_input_modality = %s, primary_output_modality = %s"):
            self.db.update_item_details(params)
            self._last_row = None
        elif normalized.startswith("insert into item_synonym"):
            self.db.insert_synonym(params)
            self._last_row = None
        elif normalized.startswith("insert into item_mechanism"):
            self._last_row = None
        elif normalized.startswith("insert into item_technique"):
            self._last_row = None
        elif normalized.startswith("insert into item_target_process"):
            self._last_row = None
        elif normalized.startswith("delete from item_facet where item_id = %s"):
            self._last_row = None
        elif normalized.startswith("insert into item_facet"):
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
        elif normalized.startswith("select id from workflow_template where slug = %s"):
            self._last_row = self.db.find_workflow_template_id(params[0])
        elif normalized.startswith("delete from workflow_mechanism where workflow_template_id = %s"):
            self._last_row = None
        elif normalized.startswith("insert into workflow_mechanism"):
            self._last_row = None
        elif normalized.startswith("delete from workflow_technique where workflow_template_id = %s"):
            self._last_row = None
        elif normalized.startswith("insert into workflow_technique"):
            self._last_row = None
        elif normalized.startswith("insert into workflow_stage_template"):
            self._last_row = (self.db.upsert_workflow_stage(params),)
        elif normalized.startswith("select id from workflow_stage_template where workflow_template_id = %s and stage_order = %s"):
            self._last_row = self.db.find_workflow_stage_id_by_order(*params)
        elif normalized.startswith("delete from workflow_edge where workflow_template_id = %s"):
            self._last_row = None
        elif normalized.startswith("insert into workflow_edge"):
            self._last_row = None
        elif normalized.startswith("delete from workflow_item_role where workflow_template_id = %s"):
            self._last_row = None
        elif normalized.startswith("insert into workflow_item_role"):
            self._last_row = None
        elif normalized.startswith("delete from workflow_assumption"):
            self.db.delete_workflow_assumption(params)
            self._last_row = None
        elif normalized.startswith("insert into workflow_assumption"):
            self.db.insert_workflow_assumption(params)
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
        self.workflow_templates = {}
        self.workflow_stages = {}
        self.synonyms = []
        self.claims = []
        self.claim_metrics = []
        self.claim_subject_links = []
        self.item_citations = []
        self.workflow_assumptions = []
        self._next_source_document_id = 1
        self._next_item_id = 1
        self._next_workflow_template_id = 1
        self._next_workflow_stage_id = 1
        self._next_claim_id = 1

    def seed_item(self, slug):
        item_id = f"item-{self._next_item_id}"
        self._next_item_id += 1
        self.items[slug] = {
            "id": item_id,
            "slug": slug,
            "item_type": "protein_domain",
            "summary": None,
            "primary_input_modality": None,
            "primary_output_modality": None,
        }
        return item_id

    def seed_workflow_template(self, slug):
        workflow_id = f"workflow-{self._next_workflow_template_id}"
        self._next_workflow_template_id += 1
        self.workflow_templates[slug] = {"id": workflow_id, "slug": slug}
        return workflow_id

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

    def find_item_type(self, item_id):
        for row in self.items.values():
            if row["id"] == item_id:
                return (row.get("item_type"),)
        return None

    def find_item_details(self, item_id):
        for row in self.items.values():
            if row["id"] == item_id:
                return (
                    row.get("summary"),
                    row.get("primary_input_modality"),
                    row.get("primary_output_modality"),
                )
        return None

    def find_workflow_template_id(self, slug):
        row = self.workflow_templates.get(slug)
        return (row["id"],) if row else None

    def upsert_item(self, params):
        slug = params[0]
        existing = self.items.get(slug)
        if existing:
            if existing.get("summary") is None:
                existing["summary"] = params[3]
            return existing["id"]
        item_id = f"item-{self._next_item_id}"
        self._next_item_id += 1
        self.items[slug] = {
            "id": item_id,
            "slug": slug,
            "canonical_name": params[1],
            "item_type": params[2],
            "summary": params[3],
            "primary_input_modality": params[6],
            "primary_output_modality": params[7],
        }
        return item_id

    def update_item_type(self, params):
        proposed_item_type, item_id = params
        for row in self.items.values():
            if row["id"] == item_id:
                row["item_type"] = proposed_item_type
                return

    def update_item_details(self, params):
        summary, primary_input_modality, primary_output_modality, item_id = params
        for row in self.items.values():
            if row["id"] == item_id:
                row["summary"] = summary
                row["primary_input_modality"] = primary_input_modality
                row["primary_output_modality"] = primary_output_modality
                return

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

    def upsert_workflow_stage(self, params):
        key = (params[0], params[3])
        existing = self.workflow_stages.get(key)
        if existing:
            existing["params"] = params
            return existing["id"]
        stage_id = f"workflow-stage-{self._next_workflow_stage_id}"
        self._next_workflow_stage_id += 1
        self.workflow_stages[key] = {"id": stage_id, "params": params}
        return stage_id

    def find_workflow_stage_id_by_order(self, workflow_template_id, stage_order):
        row = self.workflow_stages.get((workflow_template_id, stage_order))
        return (row["id"],) if row else None

    def delete_workflow_assumption(self, params):
        stage_id, source_document_id, assumption_kind = params
        self.workflow_assumptions = [
            row
            for row in self.workflow_assumptions
            if not (
                row["workflow_stage_template_id"] == stage_id
                and row["source_document_id"] == source_document_id
                and row["assumption_kind"] == assumption_kind
            )
        ]

    def insert_workflow_assumption(self, params):
        self.workflow_assumptions.append(
            {
                "workflow_template_id": params[0],
                "workflow_stage_template_id": params[1],
                "assumption_kind": params[2],
                "assumption_name": params[3],
                "value_text": params[4],
                "rationale": params[5],
                "source_document_id": params[6],
            }
        )


def test_execute_load_plan_applies_existing_item_claims() -> None:
    settings = get_settings()
    payload = json.loads(Path("tests/fixtures/review_extract_v1.sample.json").read_text())
    normalized = PacketNormalizer(settings).normalize_packet("review_extract_v1", payload)
    load_plan = LoadPlanBuilder(settings).build_from_normalized_payload(normalized)

    fake_db = FakeDatabase()
    fake_db.seed_item("aslov2")
    fake_db.seed_item("cry2-cib1")
    fake_db.seed_workflow_template("fast-no-cloning-screen")
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(fake_db))

    result = executor.execute_load_plan(load_plan, apply=True)

    assert result["mode"] == "applied"
    assert result["inserted_claim_count"] == 2
    assert result["upserted_workflow_stage_count"] == 2
    assert len(fake_db.claims) == 2
    assert len(fake_db.claim_subject_links) == 2
    assert len(fake_db.item_citations) == 2
    assert len(fake_db.workflow_stages) == 2
    assert len(fake_db.workflow_assumptions) == 2
    assert fake_db.items["aslov2"]["summary"]


def test_execute_load_plan_replaces_low_information_existing_summary() -> None:
    settings = get_settings()
    fake_db = FakeDatabase()
    fake_db.seed_item("aslov2")
    fake_db.items["aslov2"]["summary"] = "the AsLOV2 domain"

    PostgresLoadPlanExecutor._maybe_update_existing_item_details(  # noqa: SLF001
        FakeCursor(fake_db),
        fake_db.items["aslov2"]["id"],
        summary="AsLOV2 enables light-gated conformational control in engineered protein fusions.",
        primary_input_modality="light",
        primary_output_modality="conformation",
    )

    assert fake_db.items["aslov2"]["summary"] == (
        "AsLOV2 enables light-gated conformational control in engineered protein fusions."
    )


def test_execute_load_plan_routes_new_candidate_to_review_queue() -> None:
    settings = get_settings()
    load_plan = {
        "source_document": {"source_type": "review", "title": "New source"},
        "actions": {
            "toolkit_items": [
                {
                    "action": "manual_candidate_review_required",
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
                    "subject_targets": [],
                    "unresolved_subject_candidates": [{"target_kind": "item_candidate", "proposed_slug": "new-tool"}],
                    "metrics": [],
                    "citation_role_suggestion": "best_review",
                }
            ],
            "workflows": [
                {
                    "action": "manual_workflow_candidate_review_required",
                    "local_id": "workflow_new",
                    "proposed_slug": "new-workflow",
                    "canonical_name": "New Workflow",
                    "stages": [],
                }
            ],
        },
    }
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(FakeDatabase()))

    result = executor.execute_load_plan(load_plan, apply=False)

    assert result["mode"] == "dry_run"
    assert result["summary"]["review_task_count"] == 3


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
            "workflows": [
                {
                    "action": "manual_workflow_stage_review_required",
                    "reason": "No workflow candidate was extracted.",
                    "stages": [{"local_id": "stage_1", "stage_name": "broad screen"}],
                }
            ],
        },
    }
    executor = PostgresLoadPlanExecutor(settings, connection=FakeConnection(FakeDatabase()))
    review_path = tmp_path / "review-output.json"

    result = executor.execute_load_plan(load_plan, apply=False, review_output_path=review_path)

    assert result["mode"] == "dry_run"
    assert result["summary"]["review_task_count"] == 3
    payload = json.loads(review_path.read_text())
    assert payload["review_queue_type"] == "curation_review_queue_v1"
    assert len(payload["tasks"]) == 3
