# SPDX-License-Identifier: Apache-2.0
"""Unit tests for MCP tools, command executor, and security guards."""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

import pytest

from conftest import load_fixture
from sns_mcp.client.command_executor import (
    ReadOnlyViolationError,
    assert_read_only,
    sanitize_input,
)
from sns_mcp.formatters.output import ToolResponse, paginate, safe_tool_call
from sns_mcp.logging_config import SensitiveFilter
from sns_mcp.tools import policy as pol_tools
from sns_mcp.tools import system as sys_tools

# ═══════════════════════════════════════════════════════
# Read-Only Guard Tests
# ═══════════════════════════════════════════════════════


class TestAssertReadOnly:
    """Tests for the read-only command guard."""

    def test_allows_read_commands(self) -> None:
        """Read commands pass without error."""
        safe_commands = [
            "FILTER SHOW",
            "NAT SHOW",
            "OBJECT SHOW",
            "SYSTEM PROPERTY",
            "ROUTE SHOW",
            "IPSECVPN SHOW CONFIG",
            "MONITOR STAT",
            "INTERFACE SHOW",
        ]
        for cmd in safe_commands:
            assert_read_only(cmd)  # Should not raise

    def test_blocks_write_commands(self) -> None:
        """Write commands raise RuntimeError."""
        write_commands = [
            "CONFIG BACKUP",
            "OBJECT ADD name=test ip=1.2.3.4",
            "OBJECT DEL name=test",
            "FILTER ADD position=1 action=pass",
            "NAT ADD position=1",
            "ROUTE ADD dst=0.0.0.0",
            "USER ADD name=hacker",
            "USER DEL name=admin",
            "SYSTEM REBOOT",
            "SYSTEM SHUTDOWN",
            "MODIFY something",
            "DELETE something",
        ]
        for cmd in write_commands:
            with pytest.raises(ReadOnlyViolationError, match="SAFETY VIOLATION"):
                assert_read_only(cmd)

    def test_case_insensitive(self) -> None:
        """Guard works regardless of case."""
        with pytest.raises(ReadOnlyViolationError):
            assert_read_only("config backup")
        with pytest.raises(ReadOnlyViolationError):
            assert_read_only("Object Add name=test")


# ═══════════════════════════════════════════════════════
# Input Sanitization Tests
# ═══════════════════════════════════════════════════════


class TestSanitizeInput:
    """Tests for input sanitization."""

    def test_valid_inputs(self) -> None:
        """Accept valid input strings."""
        assert sanitize_input("Network_LAN", "search") == "Network_LAN"
        assert sanitize_input("192.168.1.0/24", "search") == "192.168.1.0/24"
        assert sanitize_input("host-name.example", "name") == "host-name.example"

    def test_rejects_injection(self) -> None:
        """Reject command injection attempts."""
        dangerous = [
            "test; rm -rf /",
            "test$(whoami)",
            "test`id`",
            'test" && echo pwned',
            "test\nFILTER DELETE",
        ]
        for val in dangerous:
            with pytest.raises(ValueError, match="invalid characters"):
                sanitize_input(val, "search")

    def test_strips_whitespace(self) -> None:
        """Strip leading/trailing whitespace."""
        assert sanitize_input("  hello  ", "search") == "hello"

    def test_empty_string(self) -> None:
        """Accept empty string."""
        assert sanitize_input("", "search") == ""


# ═══════════════════════════════════════════════════════
# SensitiveFilter Tests
# ═══════════════════════════════════════════════════════


class TestSensitiveFilter:
    """Tests for credential scrubbing in logs."""

    def test_redacts_password(self) -> None:
        """Password strings are redacted."""
        f = SensitiveFilter()
        record = logging.LogRecord(
            "test",
            logging.INFO,
            "",
            0,
            "User password is abc123",
            None,
            None,
        )
        f.filter(record)
        assert "password" not in record.msg.lower()
        assert "***REDACTED***" in record.msg

    def test_redacts_token(self) -> None:
        """Token strings are redacted."""
        f = SensitiveFilter()
        record = logging.LogRecord(
            "test",
            logging.INFO,
            "",
            0,
            "API token = xyz789",
            None,
            None,
        )
        f.filter(record)
        assert "***REDACTED***" in record.msg

    def test_preserves_safe_messages(self) -> None:
        """Non-sensitive messages pass through."""
        f = SensitiveFilter()
        record = logging.LogRecord(
            "test",
            logging.INFO,
            "",
            0,
            "Connected to device paris-fw-01",
            None,
            None,
        )
        f.filter(record)
        assert record.msg == "Connected to device paris-fw-01"


# ═══════════════════════════════════════════════════════
# ToolResponse Tests
# ═══════════════════════════════════════════════════════


class TestToolResponse:
    """Tests for ToolResponse serialization."""

    def test_to_json(self) -> None:
        """ToolResponse serializes to valid JSON."""
        resp = ToolResponse(
            device_id="fw1",
            tool="sns_test",
            status="ok",
            data={"key": "value"},
            count=1,
        )
        json_str = resp.to_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "ok"
        assert parsed["device_id"] == "fw1"
        assert parsed["data"] == {"key": "value"}

    def test_error_response(self) -> None:
        """Error response contains capability_note."""
        resp = ToolResponse(
            device_id="fw1",
            tool="sns_test",
            status="error",
            data=None,
            capability_note="Device not found",
        )
        parsed = json.loads(resp.to_json())
        assert parsed["status"] == "error"
        assert parsed["data"] is None
        assert "not found" in parsed["capability_note"]


# ═══════════════════════════════════════════════════════
# Pagination Tests
# ═══════════════════════════════════════════════════════


class TestPagination:
    """Tests for pagination utility."""

    def test_single_page(self) -> None:
        """Items fit in one page."""
        items = list(range(50))
        page_items, pg, ps, tp = paginate(items, 1, 100)
        assert len(page_items) == 50
        assert pg == 1
        assert tp == 1

    def test_multiple_pages(self) -> None:
        """Items span multiple pages."""
        items = list(range(250))
        page_items, pg, ps, tp = paginate(items, 2, 100)
        assert len(page_items) == 100
        assert pg == 2
        assert tp == 3

    def test_last_page(self) -> None:
        """Last page may have fewer items."""
        items = list(range(250))
        page_items, pg, ps, tp = paginate(items, 3, 100)
        assert len(page_items) == 50
        assert pg == 3

    def test_empty_list(self) -> None:
        """Empty list returns one empty page."""
        page_items, pg, ps, tp = paginate([], 1, 100)
        assert len(page_items) == 0
        assert tp == 1


# ═══════════════════════════════════════════════════════
# Safe Tool Call Tests
# ═══════════════════════════════════════════════════════


class TestSafeToolCall:
    """Tests for safe_tool_call error handling."""

    def test_device_not_found(self) -> None:
        """DeviceNotFoundError becomes error JSON."""
        from sns_mcp.client.device_manager import DeviceNotFoundError

        def _raise() -> ToolResponse:
            raise DeviceNotFoundError("unknown-fw")

        result = safe_tool_call("unknown-fw", "sns_test", _raise)
        assert result.status == "error"
        assert "not configured" in (result.capability_note or "")

    def test_capability_unavailable(self) -> None:
        """CapabilityUnavailableError becomes capability_unavailable JSON."""
        from sns_mcp.client.command_executor import CapabilityUnavailableError

        def _raise() -> ToolResponse:
            raise CapabilityUnavailableError("ztna", "fw1", "Not supported on SNS 4.x")

        result = safe_tool_call("fw1", "sns_test", _raise)
        assert result.status == "capability_unavailable"

    def test_unexpected_error(self) -> None:
        """Unexpected exceptions become error JSON, never propagate."""

        def _raise() -> ToolResponse:
            raise RuntimeError("something broke")

        result = safe_tool_call("fw1", "sns_test", _raise)
        assert result.status == "error"
        assert "RuntimeError" in (result.capability_note or "")


# ═══════════════════════════════════════════════════════
# Tool Function Tests (with mocked manager)
# ═══════════════════════════════════════════════════════


class TestFilterRulesTool:
    """Tests for sns_filter_rules_list tool function."""

    def test_returns_valid_json(self, mock_manager: MagicMock) -> None:
        """Tool returns valid JSON string."""
        fixture = load_fixture("filter_show_sns4.txt")
        mock_client = MagicMock()
        mock_client.send_command.return_value = fixture
        mock_manager.get_client.return_value = mock_client

        result_json = pol_tools.sns_filter_rules_list(mock_manager, "test-fw-01")
        parsed = json.loads(result_json)
        assert parsed["status"] == "ok"
        assert parsed["count"] == 10
        assert len(parsed["data"]) == 10

    def test_action_filter(self, mock_manager: MagicMock) -> None:
        """Filter by action type."""
        fixture = load_fixture("filter_show_sns4.txt")
        mock_client = MagicMock()
        mock_client.send_command.return_value = fixture
        mock_manager.get_client.return_value = mock_client

        result_json = pol_tools.sns_filter_rules_list(
            mock_manager,
            "test-fw-01",
            action_filter="block",
        )
        parsed = json.loads(result_json)
        assert parsed["status"] == "ok"
        assert all(r["action"] == "block" for r in parsed["data"])

    def test_search_filter(self, mock_manager: MagicMock) -> None:
        """Search across rule fields."""
        fixture = load_fixture("filter_show_sns4.txt")
        mock_client = MagicMock()
        mock_client.send_command.return_value = fixture
        mock_manager.get_client.return_value = mock_client

        result_json = pol_tools.sns_filter_rules_list(
            mock_manager,
            "test-fw-01",
            search="http",
        )
        parsed = json.loads(result_json)
        assert parsed["status"] == "ok"
        assert parsed["count"] >= 1

    def test_invalid_device_id(self, mock_manager: MagicMock) -> None:
        """Invalid device returns error JSON, not exception."""
        from sns_mcp.client.device_manager import DeviceNotFoundError

        mock_manager.get_client.side_effect = DeviceNotFoundError("bad-id")

        result_json = pol_tools.sns_filter_rules_list(mock_manager, "bad-id")
        parsed = json.loads(result_json)
        assert parsed["status"] == "error"
        assert "not configured" in parsed["capability_note"]


class TestDevicesListTool:
    """Tests for sns_devices_list tool function."""

    def test_returns_no_passwords(self, sample_config: MagicMock) -> None:
        """Device list never contains passwords."""
        manager = MagicMock()
        result_json = sys_tools.sns_devices_list(sample_config, manager)
        parsed = json.loads(result_json)
        assert parsed["status"] == "ok"
        json_str = json.dumps(parsed)
        assert "test_pass" not in json_str
        assert "password" not in json_str.lower()

    def test_returns_all_devices(self, sample_config: MagicMock) -> None:
        """All configured devices are listed."""
        manager = MagicMock()
        result_json = sys_tools.sns_devices_list(sample_config, manager)
        parsed = json.loads(result_json)
        assert parsed["count"] == 2
        ids = [d["device_id"] for d in parsed["data"]]
        assert "test-fw-01" in ids
        assert "test-fw-02" in ids
