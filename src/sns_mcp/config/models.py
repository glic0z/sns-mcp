# SPDX-License-Identifier: Apache-2.0
"""Pydantic configuration models for sns-mcp."""

from __future__ import annotations

import os
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DeviceConfig(BaseModel):
    """Configuration for a single SNS device connection."""

    host: str
    port: int = 443
    user: str
    password: str
    ssl_verify_host: bool = False
    ssl_verify_peer: bool = False
    cabundle: str | None = None
    timeout: int = 30
    firmware_hint: Literal["3", "4", "5"] | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)

    @field_validator("password", mode="before")
    @classmethod
    def resolve_env(cls, v: str) -> str:
        """Resolve ${ENV_VAR} patterns in string values."""
        if not isinstance(v, str):
            return v
        match = re.fullmatch(r"\$\{(\w+)\}", v.strip())
        if match:
            env_val = os.environ.get(match.group(1))
            if env_val is None:
                raise ValueError(f"Environment variable '{match.group(1)}' not set")
            return env_val
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is within acceptable range."""
        if not (5 <= v <= 300):
            raise ValueError("timeout must be between 5 and 300 seconds")
        return v


class ServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = "sns-mcp"
    version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8765
    path: str = "/mcp"


class CapabilitiesConfig(BaseModel):
    """Capability probing configuration."""

    probe_on_start: bool = True
    probe_timeout: int = 10


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    file: str | None = None


class AppConfig(BaseModel):
    """Top-level application configuration."""

    devices: dict[str, DeviceConfig]
    server: ServerConfig = Field(default_factory=ServerConfig)
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @model_validator(mode="after")
    def at_least_one_device(self) -> AppConfig:
        """Ensure at least one device is configured."""
        if not self.devices:
            raise ValueError("At least one device must be configured")
        return self
