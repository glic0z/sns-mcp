# SPDX-License-Identifier: Apache-2.0
"""Parser for NAT SHOW response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class NatRuleParser(BaseParser):
    """Parse NAT SHOW responses into structured NAT rule dicts.

    Handles SNS 3.x/4.x and 5.x response formats.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse NAT SHOW response into a list of NAT rule dicts.

        Args:
            data: Raw response data from NAT SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized NAT rule dictionaries.
        """
        rules: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            rules.append(cls._parse_rule(raw, firmware_version))

        return rules

    @classmethod
    def _parse_rule(cls, raw: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse a single raw NAT rule dict into a normalized structure.

        Args:
            raw: Raw rule data from the SNS response.
            firmware_version: Major firmware version string.

        Returns:
            Normalized NAT rule dictionary.
        """
        return {
            "name": str(raw.get("rulename", raw.get("name", ""))),
            "rank": int(raw.get("rank", 0)),
            "enabled": raw.get("status", "on") == "on",
            "original_source": str(raw.get("origsrc", raw.get("srchost", ""))),
            "original_destination": str(raw.get("origdst", raw.get("dsthost", ""))),
            "original_port": str(raw.get("origport", raw.get("dstport", ""))),
            "translated_source": str(raw.get("transsrc", raw.get("natsrc", ""))),
            "translated_destination": str(raw.get("transdst", raw.get("natdst", ""))),
            "translated_port": str(raw.get("transport", raw.get("natport", ""))),
            "protocol": str(raw.get("proto", "")),
            "interface": str(raw.get("iface", "")),
            "comment": str(raw.get("comment", "")),
        }
