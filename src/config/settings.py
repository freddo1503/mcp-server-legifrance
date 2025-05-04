"""
Settings module for the MCP Server.

This module defines the configuration structure using Pydantic models
and loads configuration from environment variables and YAML files.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent


class LegifranceSettings(BaseModel):
    """Settings for the Legifrance API."""

    api_url: str = Field(
        default="https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app",
        description="URL of the Legifrance API",
    )
    client_id: str = Field(default="", description="Client ID for the Legifrance API")
    client_secret: str = Field(
        default="", description="Client secret for the Legifrance API"
    )
    token_url: str = Field(
        default="https://sandbox-oauth.gouv.fr/api/oauth/token",
        description="Token URL for the Legifrance API",
    )


class ServerSettings(BaseModel):
    """Settings for the MCP Server."""

    host: str = Field(default="localhost", description="Host for the MCP Server")
    port: int = Field(default=8080, description="Port for the MCP Server")


class ApiSettings(BaseModel):
    """Settings for the development API."""

    key: str = Field(default="", description="API key for the development API")
    url: str = Field(default="", description="URL for the development API")


class LoggingSettings(BaseModel):
    """Settings for the logging system."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format",
    )
    file_enabled: bool = Field(default=False, description="Whether to log to a file")
    file_path: str | None = Field(default=None, description="Path to the log file")
    file_max_bytes: int = Field(
        default=10485760,  # 10 MB
        description="Maximum size of the log file before rotation",
    )
    file_backup_count: int = Field(
        default=5, description="Number of backup log files to keep"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate that the logging level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()


class ToolSchema(BaseModel):
    """Schema for a tool in the YAML configuration."""

    type: str
    properties: dict[str, Any]
    required: list[str] | None = None


class ToolConfig(BaseModel):
    """Configuration for a tool in the YAML configuration."""

    name: str
    description: str
    input_schema: dict[str, Any] = Field(alias="inputSchema")


class PromptMessage(BaseModel):
    """Message in a prompt configuration."""

    role: str
    content: list[dict[str, str]]


class PromptConfig(BaseModel):
    """Configuration for a prompt in the YAML configuration."""

    messages: list[PromptMessage]


class YamlConfig(BaseModel):
    """Configuration loaded from the YAML file."""

    tools: dict[str, ToolConfig]
    prompts: dict[str, PromptConfig]


class Settings(BaseModel):
    """Main settings class that combines all configuration sources."""

    legifrance: LegifranceSettings = Field(default_factory=LegifranceSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    yaml_config: YamlConfig | None = None


def create_settings() -> Settings:
    """
    Create and return the settings object.

    This function:
    1. Loads environment variables
    2. Loads YAML configuration
    3. Creates a Settings object with values from both sources

    Returns:
        Settings object with the combined configuration
    """
    # Create settings with environment variables
    settings = Settings(
        legifrance=LegifranceSettings(
            api_url=os.getenv("LEGIFRANCE_API_URL", LegifranceSettings().api_url),
            client_id=os.getenv("LEGIFRANCE_CLIENT_ID", ""),
            client_secret=os.getenv("LEGIFRANCE_CLIENT_SECRET", ""),
            token_url=os.getenv("LEGIFRANCE_TOKEN_URL", LegifranceSettings().token_url),
        ),
        server=ServerSettings(
            host=os.getenv("MCP_SERVER_HOST", ServerSettings().host),
            port=int(os.getenv("MCP_SERVER_PORT", str(ServerSettings().port))),
        ),
        api=ApiSettings(
            key=os.getenv("DEV_API_KEY", "development_key"),
            url=os.getenv("DEV_API_URL", "development_key"),
        ),
        logging=LoggingSettings(
            level=os.getenv("LOG_LEVEL", LoggingSettings().level),
            format=os.getenv("LOG_FORMAT", LoggingSettings().format),
            file_enabled=os.getenv("LOG_FILE_ENABLED", "").lower() == "true",
            file_path=os.getenv("LOG_FILE_PATH"),
            file_max_bytes=int(
                os.getenv("LOG_FILE_MAX_BYTES", str(LoggingSettings().file_max_bytes))
            ),
            file_backup_count=int(
                os.getenv(
                    "LOG_FILE_BACKUP_COUNT", str(LoggingSettings().file_backup_count)
                )
            ),
        ),
    )

    return settings


settings = create_settings()
