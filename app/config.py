"""Application settings, loaded once from environment variables / the .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration.

    Field names map to environment variables case-insensitively
    (e.g. DATABASE_URL -> database_url). Unknown env vars are ignored.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Owner connection (can write). Used only by migrations, seeding and the
    # work-order endpoints where a human submits/approves.
    database_url: str
    # Read-only connection (SELECT only). Everything the LLM can trigger — the
    # agent's tools — goes through this one, so a prompt injection cannot write.
    database_url_readonly: str

    # LLM access via OpenRouter (OpenAI-compatible API).
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str
    # Separate model for LLM-as-judge evals; None = same as llm_model (self-preference bias).
    judge_model: str | None = None

    # Langfuse tracing (phase 7). Both keys empty = tracing disabled.
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Embedding model used for RAG (phase 3).
    embedding_model: str = "intfloat/multilingual-e5-base"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the .env is read only once."""
    return Settings()
