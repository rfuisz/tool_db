from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "BioControl Toolkit API"
    app_env: str = "development"
    database_url: str = ""
    render_database_url: str = ""
    render_api_key: str = ""
    render_postgres_id: str = ""
    render_postgres_name: str = "tool-db-postgres"
    llm_api_key: str = Field(default="", validation_alias=AliasChoices("OPENAI_API_KEY", "LLM_API_KEY"))
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("OPENAI_BASE_URL", "LLM_BASE_URL"),
    )
    llm_model: str = Field(default="gpt-5.4", validation_alias=AliasChoices("OPENAI_MODEL", "LLM_MODEL"))
    llm_cache_enabled: bool = True
    llm_max_concurrency: int = 64
    llm_retry_attempts: int = 3
    llm_retry_base_delay_seconds: float = 1.0
    llm_retry_max_delay_seconds: float = 8.0
    europe_pmc_base_url: str = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    openalex_base_url: str = "https://api.openalex.org"
    openalex_mailto: str = ""
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"
    semantic_scholar_api_key: str = ""
    clinicaltrials_base_url: str = "https://clinicaltrials.gov/api/v2"
    gap_map_base_url: str = "https://www.gap-map.org"
    optobase_base_url: str = "https://optobase.org"
    api_cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    repo_root: Path = Field(default_factory=_default_repo_root)

    @property
    def knowledge_root(self) -> Path:
        return self.repo_root / "knowledge"

    @property
    def schema_root(self) -> Path:
        return self.repo_root / "schemas"

    @property
    def raw_payload_root(self) -> Path:
        return self.repo_root / "data" / "raw"

    @property
    def review_queue_root(self) -> Path:
        return self.repo_root / "data" / "review-queue"

    @property
    def pipeline_artifact_root(self) -> Path:
        return self.repo_root / "data" / "pipeline-artifacts"

    @property
    def extraction_root(self) -> Path:
        return self.repo_root / "data" / "extractions"

    @property
    def llm_cache_root(self) -> Path:
        return self.repo_root / "data" / "llm-cache"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
