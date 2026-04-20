# SPDX-License-Identifier: Apache-2.0
"""Parser for INTERFACE SHOW response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class InterfaceParser(BaseParser):
    """Parse INTERFACE SHOW responses into structured interface dicts.

    Handles physical, VLAN, bridge, LACP, loopback, and tunnel interfaces.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse INTERFACE SHOW response into a list of interface dicts.

        Args:
            data: Raw response data from INTERFACE SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized interface dictionaries.
        """
        interfaces: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            interfaces.append(cls._parse_interface(raw))

        return interfaces

    @classmethod
    def _parse_interface(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse a single raw interface dict.

        Args:
            raw: Raw interface data from the SNS response.

        Returns:
            Normalized interface dictionary.
        """
        return {
            "name": str(raw.get("name", "")),
            "type": str(raw.get("type", cls._infer_type(raw.get("name", "")))),
            "status": str(raw.get("status", raw.get("state", ""))),
            "ip": str(raw.get("ip", raw.get("addr", ""))),
            "mask": str(raw.get("mask", "")),
            "mac": str(raw.get("mac", "")),
            "speed": str(raw.get("speed", "")),
            "mtu": str(raw.get("mtu", "")),
            "zone": str(raw.get("zone", raw.get("protect", ""))),
            "vlan_id": str(raw.get("vlanid", raw.get("vlan", ""))),
            "comment": str(raw.get("comment", "")),
        }

    @classmethod
    def _infer_type(cls, name: str) -> str:
        """Infer interface type from its name.

        Args:
            name: Interface name string.

        Returns:
            Inferred type string.
        """
        lower = name.lower()
        if lower.startswith("vlan"):
            return "vlan"
        if lower.startswith("br"):
            return "bridge"
        if lower.startswith("lo"):
            return "loopback"
        if lower.startswith("tun"):
            return "tunnel"
        if lower.startswith("eth") or lower.startswith("em"):
            return "ethernet"
        return "other"
