# SPDX-License-Identifier: Apache-2.0
"""Parser for FILTER SHOW response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class FilterRuleParser(BaseParser):
    """Parse FILTER SHOW responses into structured filter rule dicts.

    Handles both SNS 3.x/4.x and 5.x response formats. The parser
    normalizes field names across firmware versions.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse FILTER SHOW response into a list of rule dicts.

        Args:
            data: Raw response data from FILTER SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized filter rule dictionaries.
        """
        rules: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            rules.append(cls._parse_rule(raw, firmware_version))

        return rules

    @classmethod
    def _parse_rule(cls, raw: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse a single raw rule dict into a normalized structure.

        Args:
            raw: Raw rule data from the SNS response.
            firmware_version: Major firmware version string.

        Returns:
            Normalized rule dictionary.
        """
        return {
            "name": str(raw.get("rulename", raw.get("name", ""))),
            "rank": int(raw.get("rank", 0)),
            "enabled": raw.get("status", "on") == "on",
            "action": str(raw.get("action", "")),
            "source": {
                "hosts": cls._parse_list(raw.get("srchost", "")),
                "interface": str(raw.get("srciface", "")),
                "user": str(raw.get("srcuser", "")),
            },
            "destination": {
                "hosts": cls._parse_list(raw.get("dsthost", "")),
                "interface": str(raw.get("dstiface", "")),
            },
            "service": cls._parse_list(raw.get("dstserv", "")),
            "schedule": str(raw.get("schedule", "always")),
            "inspection": str(raw.get("inspection", "")),
            "nat": str(raw.get("nat", "")),
            "log": str(raw.get("log", "")),
            "comment": str(raw.get("comment", "")),
        }
