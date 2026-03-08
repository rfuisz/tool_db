from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
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
    openalex_base_url: str = "https://api.openalex.org"
    openalex_mailto: str = ""
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"
    semantic_scholar_api_key: str = ""
    clinicaltrials_base_url: str = "https://clinicaltrials.gov/api/query"
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
