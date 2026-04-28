"""Centralized configuration loaded from environment variables.

All other modules import settings from here so we have one source of truth
for model names, thresholds, and tracking URIs.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM Provider ---
    anthropic_api_key: str = ""

    # --- Model selection ---
    agent_model: str = "claude-sonnet-4-5"
    judge_primary_model: str = "claude-sonnet-4-5"
    judge_secondary_model: str = "claude-haiku-4-5"

    # --- MLflow ---
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "banksafe-compliance-agent"

    # --- Eval gating thresholds ---
    eval_regression_threshold: float = 0.05
    eval_fail_on_pii_leak: bool = True
    eval_fail_on_hallucination_rate: float = 0.10


settings = Settings()
