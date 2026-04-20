# SPDX-License-Identifier: Apache-2.0
"""Unit tests for capability probing and registry."""

from __future__ import annotations

from unittest.mock import MagicMock

from sns_mcp.capabilities.probe import CAPABILITY_PROBES, probe_device
from sns_mcp.capabilities.registry import CapabilityRegistry
from sns_mcp.client.sns_client import SNSResponse


class TestProbeDevice:
    """Tests for the probe_device function."""

    def test_all_probes_succeed(self) -> None:
        """All capabilities available when all probes return OK."""
        client = MagicMock()
        client.send_command.return_value = SNSResponse(ret="00a00100")
        result = probe_device("test-fw", client)
        assert all(result.values())
        assert len(result) == len(CAPABILITY_PROBES)

    def test_all_probes_fail(self) -> None:
        """All capabilities unavailable when probes fail."""
        client = MagicMock()
        client.send_command.side_effect = ConnectionError("unreachable")
        result = probe_device("test-fw", client)
        assert not any(result.values())

    def test_mixed_results(self) -> None:
        """Some capabilities available, others not."""
        call_count = 0

        def alternating_response(cmd: str) -> SNSResponse:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                return SNSResponse(ret="00b00013")  # Not licensed
            return SNSResponse(ret="00a00100")  # OK

        client = MagicMock()
        client.send_command.side_effect = alternating_response
        result = probe_device("test-fw", client)
        available = sum(1 for v in result.values() if v)
        unavailable = sum(1 for v in result.values() if not v)
        assert available > 0
        assert unavailable > 0

    def test_begin_code_treated_as_ok(self) -> None:
        """Streaming 'Begin' code should be treated as available."""
        client = MagicMock()
        client.send_command.return_value = SNSResponse(ret="00a01000")
        result = probe_device("test-fw", client)
        assert all(result.values())


class TestCapabilityRegistry:
    """Tests for CapabilityRegistry."""

    def test_is_available(self) -> None:
        """Check capability availability."""
        registry = CapabilityRegistry()
        registry.load(
            {
                "fw1": {"filter": True, "vpn_ipsec": False},
                "fw2": {"filter": True, "vpn_ipsec": True},
            }
        )
        assert registry.is_available("fw1", "filter") is True
        assert registry.is_available("fw1", "vpn_ipsec") is False
        assert registry.is_available("fw2", "vpn_ipsec") is True

    def test_any_device_has(self) -> None:
        """Check if any device supports a capability."""
        registry = CapabilityRegistry()
        registry.load(
            {
                "fw1": {"filter": True, "ztna": False},
                "fw2": {"filter": True, "ztna": True},
            }
        )
        assert registry.any_device_has("ztna") is True
        assert registry.any_device_has("nonexistent") is False

    def test_unknown_device(self) -> None:
        """Unknown device returns False for all capabilities."""
        registry = CapabilityRegistry()
        registry.load({"fw1": {"filter": True}})
        assert registry.is_available("unknown", "filter") is False

    def test_empty_registry(self) -> None:
        """Empty registry returns False."""
        registry = CapabilityRegistry()
        assert registry.is_available("fw1", "filter") is False
        assert registry.any_device_has("filter") is False
