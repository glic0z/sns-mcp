# SPDX-License-Identifier: Apache-2.0
"""Parsers for OBJECT and SERVICE SHOW response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class ObjectParser(BaseParser):
    """Parse OBJECT SHOW responses into structured network object dicts.

    Handles host, network, range, and FQDN objects across
    SNS 3.x/4.x/5.x firmware versions.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse OBJECT SHOW response into a list of object dicts.

        Args:
            data: Raw response data from OBJECT SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized network object dictionaries.
        """
        objects: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            objects.append(cls._parse_object(raw))

        return objects

    @classmethod
    def _parse_object(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse a single raw object dict.

        Args:
            raw: Raw object data from the SNS response.

        Returns:
            Normalized network object dictionary.
        """
        return {
            "name": str(raw.get("name", "")),
            "type": str(raw.get("type", "")),
            "ip": str(raw.get("ip", raw.get("addr", ""))),
            "mask": str(raw.get("mask", "")),
            "begin": str(raw.get("begin", "")),
            "end": str(raw.get("end", "")),
            "fqdn": str(raw.get("fqdn", "")),
            "comment": str(raw.get("comment", "")),
            "builtin": raw.get("builtin", "0") == "1",
            "color": str(raw.get("color", "")),
        }


class ObjectGroupParser(BaseParser):
    """Parse OBJECT GROUP SHOW responses into structured group dicts."""

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse OBJECT GROUP SHOW response into a list of group dicts.

        Args:
            data: Raw response data from OBJECT GROUP SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized group dictionaries.
        """
        groups: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            groups.append(
                {
                    "name": str(raw.get("name", "")),
                    "members": cls._parse_list(raw.get("member", raw.get("members", ""))),
                    "comment": str(raw.get("comment", "")),
                    "builtin": raw.get("builtin", "0") == "1",
                }
            )

        return groups


class ServiceParser(BaseParser):
    """Parse SERVICE SHOW responses into structured service object dicts."""

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]]:
        """Parse SERVICE SHOW response into a list of service dicts.

        Args:
            data: Raw response data from SERVICE SHOW.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized service object dictionaries.
        """
        services: list[dict[str, Any]] = []
        result_list = cls._get_result_list(data)

        for raw in result_list:
            services.append(cls._parse_service(raw))

        return services

    @classmethod
    def _parse_service(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse a single raw service dict.

        Args:
            raw: Raw service data from the SNS response.

        Returns:
            Normalized service object dictionary.
        """
        return {
            "name": str(raw.get("name", "")),
            "protocol": str(raw.get("proto", raw.get("protocol", ""))),
            "port": str(raw.get("port", raw.get("dstport", ""))),
            "port_range": str(raw.get("portrange", "")),
            "comment": str(raw.get("comment", "")),
            "builtin": raw.get("builtin", "0") == "1",
        }
