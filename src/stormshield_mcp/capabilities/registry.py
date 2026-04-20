# SPDX-License-Identifier: Apache-2.0
"""Per-device capability cache and lookup."""

from __future__ import annotations

import logging

logger = logging.getLogger("stormshield_mcp.capabilities.registry")


class CapabilityRegistry:
    """Stores and queries per-device capability availability.

    After probing, this registry is used by tools to check whether
    a given capability is available on a specific device before
    attempting to execute commands.
    """

    def __init__(self) -> None:
        """Initialize an empty capability registry."""
        self._capabilities: dict[str, dict[str, bool]] = {}

    def load(self, device_capabilities: dict[str, dict[str, bool]]) -> None:
        """Load probed capabilities for all devices.

        Args:
            device_capabilities: Mapping of device_id to capability booleans.
        """
        self._capabilities = dict(device_capabilities)

    def is_available(self, device_id: str, capability: str) -> bool:
        """Check if a capability is available on a specific device.

        Args:
            device_id: The device identifier.
            capability: The capability key (e.g., 'filter', 'vpn_ipsec').

        Returns:
            True if the capability is available on the device.
        """
        device_caps = self._capabilities.get(device_id, {})
        return device_caps.get(capability, False)

    def any_device_has(self, capability: str) -> bool:
        """Check if any configured device supports a capability.

        Args:
            capability: The capability key.

        Returns:
            True if at least one device supports the capability.
        """
        return any(caps.get(capability, False) for caps in self._capabilities.values())

    def get_device_capabilities(self, device_id: str) -> dict[str, bool]:
        """Get all capabilities for a specific device.

        Args:
            device_id: The device identifier.

        Returns:
            Dictionary mapping capability keys to availability booleans.
        """
        return dict(self._capabilities.get(device_id, {}))

    def get_all(self) -> dict[str, dict[str, bool]]:
        """Get all device capabilities.

        Returns:
            Full capabilities mapping.
        """
        return dict(self._capabilities)
