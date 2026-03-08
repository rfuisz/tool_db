from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from tool_db_backend.config import Settings, get_settings
from tool_db_backend.models import (
    FirstPassItemDetail,
    FirstPassItemSummary,
    HealthResponse,
    ItemDetail,
    ItemSummary,
    SourceRegistryEntry,
    VocabularyPayload,
    WorkflowDetail,
    WorkflowSummary,
)
from tool_db_backend.repository import KnowledgeRepository


def get_repository(settings: Settings = Depends(get_settings)) -> KnowledgeRepository:
    return KnowledgeRepository(settings)


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

    @app.get("/api/v1/items/{slug}", response_model=ItemDetail)
    def get_item(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> ItemDetail:
        try:
            return repo.get_item(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown item slug: {slug}") from exc

    @app.get("/api/v1/first-pass-items", response_model=list[FirstPassItemSummary])
    def list_first_pass_items(repo: KnowledgeRepository = Depends(get_repository)) -> list[FirstPassItemSummary]:
        return repo.list_first_pass_items()

    @app.get("/api/v1/first-pass-items/{slug}", response_model=FirstPassItemDetail)
    def get_first_pass_item(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> FirstPassItemDetail:
        try:
            return repo.get_first_pass_item(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown first-pass item slug: {slug}") from exc

    @app.get("/api/v1/workflows", response_model=list[WorkflowSummary])
    def list_workflows(repo: KnowledgeRepository = Depends(get_repository)) -> list[WorkflowSummary]:
        return repo.list_workflows()

    @app.get("/api/v1/workflows/{slug}", response_model=WorkflowDetail)
    def get_workflow(slug: str, repo: KnowledgeRepository = Depends(get_repository)) -> WorkflowDetail:
        try:
            return repo.get_workflow(slug)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown workflow slug: {slug}") from exc

    return app


app = create_app()
