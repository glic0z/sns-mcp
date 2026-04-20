# SPDX-License-Identifier: Apache-2.0
"""YAML configuration loading with environment variable injection."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from .models import AppConfig

_DEFAULT_CONFIG_PATHS = [
    Path("config/config.yaml"),
    Path("config.yaml"),
]


def _resolve_env_vars_in_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively resolve ${ENV_VAR} patterns in all string values."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = _resolve_env_string(value)
        elif isinstance(value, dict):
            result[key] = _resolve_env_vars_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _resolve_env_string(item) if isinstance(item, str) else item for item in value
            ]
        else:
            result[key] = value
    return result


def _resolve_env_string(value: str) -> str:
    """Resolve ${ENV_VAR} in a single string value."""
    pattern = re.compile(r"\$\{(\w+)\}")
    match = pattern.fullmatch(value.strip())
    if match:
        env_val = os.environ.get(match.group(1))
        if env_val is not None:
            return env_val
    return value


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    """Apply SNS_MCP_* environment variable overrides.

    Pattern: SNS_MCP_DEVICE__<DEVICE_ID>__<FIELD>=value
             SNS_MCP_SERVER__<FIELD>=value
             SNS_MCP_LOGGING__<FIELD>=value
    """
    prefix = "SNS_MCP_"
    for env_key, env_val in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        parts = env_key[len(prefix) :].split("__")

        if len(parts) == 3 and parts[0].upper() == "DEVICE":
            device_id = parts[1].lower()
            field = parts[2].lower()
            if "devices" not in data:
                data["devices"] = {}
            if device_id not in data["devices"]:
                data["devices"][device_id] = {}
            data["devices"][device_id][field] = env_val

        elif len(parts) == 2:
            section = parts[0].lower()
            field = parts[1].lower()
            if section not in data:
                data[section] = {}
            if isinstance(data[section], dict):
                data[section][field] = env_val

    return data


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load and validate configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file. If None, searches
                     default locations.

    Returns:
        Validated AppConfig instance.

    Raises:
        FileNotFoundError: If no configuration file is found.
        ValueError: If the configuration is invalid.
    """
    path: Path | None = None

    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
    else:
        for default_path in _DEFAULT_CONFIG_PATHS:
            if default_path.exists():
                path = default_path
                break
        if path is None:
            raise FileNotFoundError(
                "No configuration file found. Searched: "
                + ", ".join(str(p) for p in _DEFAULT_CONFIG_PATHS)
            )

    with open(path, encoding="utf-8") as fh:
        raw_data: dict[str, Any] = yaml.safe_load(fh) or {}

    raw_data = _resolve_env_vars_in_dict(raw_data)
    raw_data = _apply_env_overrides(raw_data)

    return AppConfig.model_validate(raw_data)
