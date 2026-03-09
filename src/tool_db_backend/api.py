import gzip

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from tool_db_backend.config import Settings, get_settings
from tool_db_backend.models import (
    ExtractedWorkflowSummary,
    FirstPassEntityDetail,
    FirstPassEntitySummary,
    FirstPassItemDetail,
    FirstPassItemSummary,
    GapDetail,
    GapSummary,
    HealthResponse,
    ItemBrowse,
    ItemDetail,
    ItemSummary,
    SourceRegistryEntry,
    VocabularyPayload,
    WorkflowDetail,
    WorkflowSummary,
)
from tool_db_backend.render_db_sync import (
    RenderDbSyncError,
    get_database_import_preflight,
    get_render_database_sync_preflight,
    import_sql_dump_into_database,
    sync_render_database,
)
from tool_db_backend.repository import KnowledgeRepository


def get_repository(settings: Settings = Depends(get_settings)) -> KnowledgeRepository:
    return KnowledgeRepository(settings)


def _is_local_admin_request(request: Request, settings: Settings) -> bool:
    if settings.app_env != "development":
        return False
    host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    hostname = host_header.split(":")[0].strip().lower()
    return hostname in {"localhost", "127.0.0.1"}


def _get_admin_sync_key(settings: Settings) -> str:
    return settings.admin_sync_key.strip()


def _is_sync_key_request(request: Request, settings: Settings) -> bool:
    required_key = _get_admin_sync_key(settings)
    if not required_key:
        return False

    authorization_header = (request.headers.get("authorization") or "").strip()
    if authorization_header.lower().startswith("bearer "):
        authorization_header = authorization_header[7:].strip()

    provided_key = (request.headers.get("x-api-key") or authorization_header).strip()
    return provided_key == required_key


def _require_local_admin_or_sync_key(request: Request, settings: Settings) -> None:
    if _is_local_admin_request(request, settings) or _is_sync_key_request(request, settings):
        return

    if _get_admin_sync_key(settings):
        raise HTTPException(
            status_code=401,
            detail="Provide a valid sync key via x-api-key or Authorization: Bearer.",
        )

    raise HTTPException(
        status_code=403,
        detail="Hosted database import is only available from localhost until TOOL_DB_ADMIN_SYNC_KEY is set.",
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", response_model=HealthResponse)
    def healthz(settings: Settings = Depends(get_settings)) -> HealthResponse:
        return HealthResponse(
            status="ok",
            app_name=settings.app_name,
            environment=settings.app_env,
        )

    @app.get("/api/v1/vocabularies", response_model=VocabularyPayload)
    def get_vocabularies(repo: KnowledgeRepository = Depends(get_repository)) -> VocabularyPayload:
        return repo.get_vocabularies()

    @app.get("/api/v1/source-registry", response_model=list[SourceRegistryEntry])
    def get_source_registry(repo: KnowledgeRepository = Depends(get_repository)) -> list[SourceRegistryEntry]:
        return repo.get_source_registry()

    @app.get("/api/v1/items", response_model=list[ItemSummary])
    def list_items(repo: KnowledgeRepository = Depends(get_repository)) -> list[ItemSummary]:
        return repo.list_items()

    @app.get("/api/v1/items-browse", response_model=list[ItemBrowse])
    def list_item_browse(repo: KnowledgeRepository = Depends(get_repository)) -> list[ItemBrowse]:
        return repo.list_item_browse()

    @app.get("/api/v1/items/{slug}", response_model=ItemDetail)
    def get_item(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> ItemDetail:
        try:
            return repo.get_item(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown item slug: {slug}") from exc

    @app.get("/api/v1/gaps", response_model=list[GapSummary])
    def list_gaps(repo: KnowledgeRepository = Depends(get_repository)) -> list[GapSummary]:
        return repo.list_gaps()

    @app.get("/api/v1/gaps/{slug}", response_model=GapDetail)
    def get_gap(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> GapDetail:
        try:
            return repo.get_gap(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown gap slug: {slug}") from exc

    @app.get("/api/v1/first-pass-items", response_model=list[FirstPassItemSummary])
    def list_first_pass_items(repo: KnowledgeRepository = Depends(get_repository)) -> list[FirstPassItemSummary]:
        return repo.list_first_pass_items()

    @app.get("/api/v1/first-pass-entities", response_model=list[FirstPassEntitySummary])
    def list_first_pass_entities(repo: KnowledgeRepository = Depends(get_repository)) -> list[FirstPassEntitySummary]:
        return repo.list_first_pass_entities()

    @app.get("/api/v1/first-pass-items/{slug}", response_model=FirstPassItemDetail)
    def get_first_pass_item(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> FirstPassItemDetail:
        try:
            return repo.get_first_pass_item(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown first-pass item slug: {slug}") from exc

    @app.get("/api/v1/first-pass-entities/{candidate_type}/{slug}", response_model=FirstPassEntityDetail)
    def get_first_pass_entity(
        candidate_type: str,
        slug: str,
        repo: KnowledgeRepository = Depends(get_repository),
    ) -> FirstPassEntityDetail:
        try:
            return repo.get_first_pass_entity(candidate_type, slug)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown first-pass entity: {candidate_type}/{slug}",
            ) from exc

    @app.get("/api/v1/workflows", response_model=list[WorkflowSummary])
    def list_workflows(repo: KnowledgeRepository = Depends(get_repository)) -> list[WorkflowSummary]:
        return repo.list_workflows()

    @app.get("/api/v1/workflows/{slug}", response_model=WorkflowDetail)
    def get_workflow(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> WorkflowDetail:
        try:
            return repo.get_workflow(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown workflow slug: {slug}") from exc

    @app.get("/api/v1/extracted-workflows", response_model=list[ExtractedWorkflowSummary])
    def list_extracted_workflows(repo: KnowledgeRepository = Depends(get_repository)) -> list[ExtractedWorkflowSummary]:
        return repo.list_extracted_workflows()

    @app.post("/api/v1/admin/sync-render-db")
    def sync_render_db(request: Request, settings: Settings = Depends(get_settings)) -> dict:
        if not _is_local_admin_request(request, settings):
            raise HTTPException(status_code=403, detail="Render DB sync is only available from localhost.")
        try:
            return sync_render_database(settings)
        except RenderDbSyncError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/admin/sync-render-db")
    def get_sync_render_db_preflight(request: Request, settings: Settings = Depends(get_settings)) -> dict:
        if not _is_local_admin_request(request, settings):
            raise HTTPException(status_code=403, detail="Render DB sync is only available from localhost.")
        try:
            return get_render_database_sync_preflight(settings)
        except RenderDbSyncError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/admin/import-db")
    def get_import_db_preflight(request: Request, settings: Settings = Depends(get_settings)) -> dict:
        _require_local_admin_or_sync_key(request, settings)
        try:
            return get_database_import_preflight(settings)
        except RenderDbSyncError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/admin/import-db")
    async def import_db(request: Request, settings: Settings = Depends(get_settings)) -> dict:
        _require_local_admin_or_sync_key(request, settings)
        raw_body = await request.body()
        if not raw_body:
            raise HTTPException(status_code=400, detail="Request body must contain a SQL dump.")

        if request.headers.get("content-encoding", "").lower() == "gzip":
            try:
                raw_body = gzip.decompress(raw_body)
            except OSError as exc:
                raise HTTPException(status_code=400, detail="Could not decompress gzip SQL dump.") from exc

        try:
            sql_dump = raw_body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="SQL dump must be valid UTF-8 text.") from exc

        try:
            return import_sql_dump_into_database(settings, sql_dump)
        except RenderDbSyncError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
