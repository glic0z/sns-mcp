# SPDX-License-Identifier: Apache-2.0
"""Shared test fixtures and mock SNS client."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from sns_mcp.client.sns_client import SNSResponse
from sns_mcp.config.models import AppConfig, DeviceConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def parse_fixture(raw: str) -> SNSResponse:
    """Parse a fixture file into an SNSResponse object.

    Handles both 'section' (key=value dict) and 'section_line'
    (repeated line entries) formats from SNS CLI output.

    Args:
        raw: Raw fixture text content.

    Returns:
        SNSResponse with parsed data.
    """
    lines = raw.strip().splitlines()

    # Parse header line
    ret = ""
    fmt = "section"
    msg = ""
    if lines:
        header = lines[0]
        code_match = re.search(r"code=(\S+)", header)
        fmt_match = re.search(r'format="(\w+)"', header)
        msg_match = re.search(r'msg="([^"]*)"', header)
        if code_match:
            ret = code_match.group(1)
        if fmt_match:
            fmt = fmt_match.group(1)
        if msg_match:
            msg = msg_match.group(1)

    # Parse footer for final return code
    final_ret = ret
    if len(lines) >= 2:
        footer = lines[-1]
        footer_code = re.search(r"code=(\S+)", footer)
        if footer_code:
            final_ret = footer_code.group(1)

    # Parse result section
    data: dict[str, Any] = {}
    in_result = False
    result_items: list[dict[str, str]] = []

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("[Result]"):
            in_result = True
            continue
        if stripped.startswith("100 ") or stripped.startswith("200 "):
            break
        if not in_result or not stripped:
            continue

        # Parse key=value pairs from the line
        parsed = _parse_kv_line(stripped)
        if parsed:
            result_items.append(parsed)

    if fmt == "section":
        flattened: dict[str, str] = {}
        for item in result_items:
            flattened.update(item)
        data["Result"] = flattened
    elif fmt == "section_line":
        data["Result"] = result_items
    elif len(result_items) == 0:
        data["Result"] = []
    else:
        data["Result"] = result_items[0]

    return SNSResponse(
        ret=final_ret,
        code=final_ret,
        msg=msg,
        format=fmt,
        data=data,
        raw=raw,
    )


def _parse_kv_line(line: str) -> dict[str, str]:
    """Parse a single key=value line from SNS output.

    Handles quoted values like comment="some text".

    Args:
        line: A single line of key=value pairs.

    Returns:
        Dictionary of parsed key-value pairs.
    """
    result: dict[str, str] = {}
    # Match key=value or key="quoted value"
    pattern = re.compile(r'(\w+)=(?:"([^"]*)"|(\S*))')
    for match in pattern.finditer(line):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        result[key] = value
    return result


def load_fixture(name: str) -> SNSResponse:
    """Load and parse a fixture file by name.

    Args:
        name: Fixture filename (e.g. 'filter_show_sns4.txt').

    Returns:
        Parsed SNSResponse.
    """
    path = FIXTURES_DIR / name
    raw = path.read_text(encoding="utf-8")
    return parse_fixture(raw)


@pytest.fixture
def sample_config() -> AppConfig:
    """Create a sample AppConfig for testing."""
    return AppConfig(
        devices={
            "test-fw-01": DeviceConfig(
                host="192.168.1.1",
                port=443,
                user="admin",
                password="test_pass",
                ssl_verify_host=False,
                ssl_verify_peer=False,
                timeout=30,
                firmware_hint="4",
                description="Test firewall",
                tags=["test"],
            ),
            "test-fw-02": DeviceConfig(
                host="10.0.0.1",
                port=443,
                user="monitor",
                password="test_pass2",
                ssl_verify_host=False,
                ssl_verify_peer=False,
                timeout=30,
                firmware_hint="5",
                description="Test firewall 2",
                tags=["test", "backup"],
            ),
        }
    )


@pytest.fixture
def mock_manager(sample_config: AppConfig) -> MagicMock:
    """Create a mock DeviceManager for testing tools."""
    manager = MagicMock()
    manager._config = sample_config
    manager.get_device_ids.return_value = list(sample_config.devices.keys())
    manager.get_firmware_version.return_value = "4"
    return manager
