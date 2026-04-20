# SPDX-License-Identifier: Apache-2.0
"""Unit tests for configuration loading and validation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from stormshield_mcp.config.loader import load_config
from stormshield_mcp.config.models import AppConfig, DeviceConfig


class TestDeviceConfig:
    """Tests for DeviceConfig validation."""

    def test_valid_config(self) -> None:
        """Create a valid device config."""
        cfg = DeviceConfig(
            host="192.168.1.1",
            user="admin",
            password="pass123",
        )
        assert cfg.host == "192.168.1.1"
        assert cfg.port == 443
        assert cfg.timeout == 30

    def test_timeout_too_low(self) -> None:
        """Reject timeout below 5."""
        with pytest.raises(ValueError, match="timeout"):
            DeviceConfig(host="1.2.3.4", user="u", password="p", timeout=1)

    def test_timeout_too_high(self) -> None:
        """Reject timeout above 300."""
        with pytest.raises(ValueError, match="timeout"):
            DeviceConfig(host="1.2.3.4", user="u", password="p", timeout=999)

    def test_env_var_resolution(self) -> None:
        """Resolve ${ENV_VAR} in password field."""
        os.environ["TEST_SNS_PW"] = "resolved_pass"
        try:
            cfg = DeviceConfig(
                host="1.2.3.4",
                user="u",
                password="${TEST_SNS_PW}",
            )
            assert cfg.password == "resolved_pass"
        finally:
            del os.environ["TEST_SNS_PW"]

    def test_missing_env_var(self) -> None:
        """Raise error for missing env var."""
        os.environ.pop("MISSING_VAR_XYZ", None)
        with pytest.raises(ValueError, match="Environment variable"):
            DeviceConfig(
                host="1.2.3.4",
                user="u",
                password="${MISSING_VAR_XYZ}",
            )

    def test_firmware_hint_values(self) -> None:
        """Accept valid firmware hints."""
        for hint in ["3", "4", "5"]:
            cfg = DeviceConfig(
                host="1.2.3.4",
                user="u",
                password="p",
                firmware_hint=hint,  # type: ignore[arg-type]
            )
            assert cfg.firmware_hint == hint


class TestAppConfig:
    """Tests for AppConfig validation."""

    def test_empty_devices_rejected(self) -> None:
        """Reject config with no devices."""
        with pytest.raises(ValueError, match="At least one device"):
            AppConfig(devices={})

    def test_valid_app_config(self) -> None:
        """Create a valid app config."""
        cfg = AppConfig(
            devices={
                "fw1": DeviceConfig(host="1.2.3.4", user="u", password="p"),
            }
        )
        assert "fw1" in cfg.devices
        assert cfg.server.port == 8765


class TestConfigLoader:
    """Tests for YAML config loading."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Load a valid YAML config file."""
        config_data = {
            "devices": {
                "test-fw": {
                    "host": "192.168.1.1",
                    "user": "admin",
                    "password": "testpass",
                }
            }
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        cfg = load_config(str(config_file))
        assert "test-fw" in cfg.devices
        assert cfg.devices["test-fw"].host == "192.168.1.1"

    def test_load_missing_file(self) -> None:
        """Raise error for missing config file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_env_override(self, tmp_path: Path) -> None:
        """Test SNS_MCP_ environment variable overrides."""
        config_data = {
            "devices": {
                "fw1": {
                    "host": "1.2.3.4",
                    "user": "admin",
                    "password": "p",
                }
            },
            "server": {"port": 8765},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        os.environ["SNS_MCP_SERVER__PORT"] = "9999"
        try:
            cfg = load_config(str(config_file))
            assert cfg.server.port == 9999
        finally:
            del os.environ["SNS_MCP_SERVER__PORT"]
