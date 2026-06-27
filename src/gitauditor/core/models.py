from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Repo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    host: str | None = Field(default=None, index=True)  # Ex: github.com, gitlab.com
    owner: str | None = Field(default=None, index=True)  # Ex: refernandes
    canonical_name: str | None = Field(
        default=None, index=True
    )  # Ex: github.com/refernandes/gitauditor

    # Metadados enriquecidos
    tags: str | None = Field(default="")  # Separados por vírgula ou JSON string
    size_mb: float | None = Field(default=0.0)

    # Saúde do Repositório
    remote_url: str | None = Field(default=None)
    status: str = Field(default="Unknown")  # OK, Local, Stale, Broken, Timeout
    last_activity: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # P3: Semantic Fields
    ai_summary: str | None = Field(default=None)
    ai_tags: str | None = Field(default=None)  # CSV format
    ai_stack: str | None = Field(default=None)
    ai_risk: str | None = Field(default=None)

    # P3: Governance Fields
    ai_model: str | None = Field(default=None)
    ai_prompt_version: str | None = Field(default=None)
    ai_updated_at: datetime | None = Field(default=None)
    ai_confidence: float | None = Field(default=None)
    ai_error: str | None = Field(default=None)
    ai_source_hash: str | None = Field(default=None)
