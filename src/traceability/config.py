"""Configuration loading with YAML + environment overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from traceability.domain.requirement_tag import DEFAULT_REQ_TAG_PATTERN
from traceability.exceptions import ConfigurationError


class AppSettings(BaseModel):
    name: str = "ASPICE Traceability Matrix Generator"
    environment: str = "local"
    log_level: str = "INFO"
    req_tag_pattern: str = DEFAULT_REQ_TAG_PATTERN


class DoorsSettings(BaseModel):
    base_url: str = "https://doors.example.com/dwa/api"
    username: str = ""
    password: SecretStr = SecretStr("")
    module_path: str = "/Project/Requirements"
    timeout_seconds: float = 30.0
    max_retries: int = 3


class CodebeamerSettings(BaseModel):
    base_url: str = "https://codebeamer.example.com/cb/rest"
    token: SecretStr = SecretStr("")
    project_id: int = 1000
    timeout_seconds: float = 30.0
    max_retries: int = 3


class GitSettings(BaseModel):
    provider: Literal["github", "gitlab", "azure"] = "github"
    base_url: str = "https://api.github.com"
    token: SecretStr = SecretStr("")
    owner: str = "org"
    repo: str = "ecu-firmware"
    timeout_seconds: float = 30.0
    max_retries: int = 3


class RqmSettings(BaseModel):
    base_url: str = (
        "https://rqm.example.com/qm/service/com.ibm.rqm.integration.service.IMainService"
    )
    username: str = ""
    password: SecretStr = SecretStr("")
    project_area: str = "ADAS_Validation"
    timeout_seconds: float = 45.0
    max_retries: int = 3


class MatrixSettings(BaseModel):
    output_dir: str = "artifacts"
    title: str = "ASPICE Bidirectional Traceability Matrix"
    include_orphan_requirements: bool = True
    include_orphan_tests: bool = True
    html_template: str = "matrix.html.j2"


class SyncSettings(BaseModel):
    batch_size: int = 100
    fail_fast: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TRACEABILITY__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    doors: DoorsSettings = Field(default_factory=DoorsSettings)
    codebeamer: CodebeamerSettings = Field(default_factory=CodebeamerSettings)
    git: GitSettings = Field(default_factory=GitSettings)
    rqm: RqmSettings = Field(default_factory=RqmSettings)
    matrix: MatrixSettings = Field(default_factory=MatrixSettings)
    sync: SyncSettings = Field(default_factory=SyncSettings)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load settings from YAML (optional) then apply environment overrides."""
    data: dict[str, Any] = {}
    path = Path(config_path) if config_path else None

    if path is None:
        candidates = [
            Path("config/default.yaml"),
            Path(__file__).resolve().parents[2] / "config" / "default.yaml",
        ]
        for candidate in candidates:
            if candidate.is_file():
                path = candidate
                break

    if path is not None:
        if not path.is_file():
            raise ConfigurationError(f"config file not found: {path}")
        with path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ConfigurationError("config root must be a mapping")
        data = loaded

    # Environment secrets without nested prefix convenience
    env_aliases = {
        "DOORS_PASSWORD": ("doors", "password"),
        "CODEBEAMER_TOKEN": ("codebeamer", "token"),
        "GIT_TOKEN": ("git", "token"),
        "RQM_PASSWORD": ("rqm", "password"),
    }
    import os

    for env_key, (section, field) in env_aliases.items():
        value = os.environ.get(env_key)
        if value:
            data.setdefault(section, {})[field] = value

    return Settings(**data)
