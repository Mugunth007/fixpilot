"""FixPilot configuration — loads environment variables and exposes typed settings."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class LiteLLMConfig(BaseModel):
    """Cloud LLM settings (Claude via LiteLLM)."""
    api_key: str = Field(default_factory=lambda: os.getenv("LITELLM_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: os.getenv("LITELLM_BASE_URL", "https://api.litellm.ai/v1"))
    model: str = Field(default_factory=lambda: os.getenv("LITELLM_MODEL", "claude-sonnet-4-20250514"))


class NeatlogsConfig(BaseModel):
    """neatlogs observability settings."""
    api_key: str = Field(default_factory=lambda: os.getenv("NEATLOGS_API_KEY", ""))
    org_id: str = Field(default_factory=lambda: os.getenv("NEATLOGS_ORG_ID", "db3c0208-c262-4f7b-bf77-fd7c68b2c2b3"))
    project_id: str = Field(default_factory=lambda: os.getenv("NEATLOGS_PROJECT_ID", "9e96e683-fdc1-41f9-90cf-bda9abf9b448"))
    workflow_name: str = Field(default_factory=lambda: os.getenv("NEATLOGS_WORKFLOW_NAME", "fixpilot"))


class GitHubConfig(BaseModel):
    """GitHub integration settings."""
    token: str = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))


class EntireConfig(BaseModel):
    """Entire codebase-context settings."""
    api_key: str = Field(default_factory=lambda: os.getenv("ENTIRE_API_KEY", ""))


class LocalLLMConfig(BaseModel):
    """Local Llama model settings for guardrails."""
    model_path: str = Field(default_factory=lambda: os.getenv("LOCAL_MODEL_PATH", "models/llama-3.2-3b-q4_k_m.gguf"))
    context_length: int = Field(default_factory=lambda: int(os.getenv("LOCAL_MODEL_CONTEXT_LENGTH", "4096")))
    n_threads: int = Field(default_factory=lambda: int(os.getenv("LOCAL_MODEL_THREADS", "4")))


class Settings(BaseModel):
    """Top-level application settings."""
    litellm: LiteLLMConfig = Field(default_factory=LiteLLMConfig)
    neatlogs: NeatlogsConfig = Field(default_factory=NeatlogsConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    entire: EntireConfig = Field(default_factory=EntireConfig)
    local_llm: LocalLLMConfig = Field(default_factory=LocalLLMConfig)


# Singleton — import from anywhere as `from src.config import settings`
settings = Settings()
