# SPDX-License-Identifier: Apache-2.0
"""Integration tests (require live SNS device)."""

from __future__ import annotations

import os

import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("SNS_INTEGRATION_TEST"),
    reason="Set SNS_INTEGRATION_TEST=1 and configure a real device",
)
class TestLiveDevice:
    """Integration tests that require a live SNS device."""

    def test_filter_rules_live(self) -> None:
        """Fetch filter rules from a live device."""
        # This test requires a configured device
        pytest.skip("Live device integration test — configure manually")

    def test_system_info_live(self) -> None:
        """Fetch system info from a live device."""
        pytest.skip("Live device integration test — configure manually")
