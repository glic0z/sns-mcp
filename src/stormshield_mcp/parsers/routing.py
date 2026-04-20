# SPDX-License-Identifier: Apache-2.0
"""Parser for ROUTE SHOW response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class RoutingParser(BaseParser):
    """Parse ROUTE SHOW responses into structured routing table entries.

    Handles static, dynamic, connected, and policy-based routes.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse ROUTE SHOW response into a list of route dicts.

        Args:
            data: Raw response data from ROUTE SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized routing table entry dictionaries.
        """
        routes: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            routes.append(cls._parse_route(raw))

        return routes

    @classmethod
    def _parse_route(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse a single raw route dict.

        Args:
            raw: Raw route data from the SNS response.

        Returns:
            Normalized route dictionary.
        """
        return {
            "destination": str(raw.get("dst", raw.get("destination", ""))),
            "mask": str(raw.get("mask", "")),
            "gateway": str(raw.get("gw", raw.get("gateway", ""))),
            "interface": str(raw.get("iface", raw.get("interface", ""))),
            "metric": str(raw.get("metric", "")),
            "type": str(raw.get("type", "static")),
            "comment": str(raw.get("comment", "")),
        }
