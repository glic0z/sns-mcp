# SPDX-License-Identifier: Apache-2.0
"""Parsers for SYSTEM PROPERTY, LICENSE, HA, and MONITOR responses."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class SystemPropertyParser(BaseParser):
    """Parse SYSTEM PROPERTY responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse SYSTEM PROPERTY response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            Normalized system information dictionary.
        """
        result = cls._get_result_dict(data)
        return {
            "model": str(result.get("Model", "")),
            "version": str(result.get("Version", "")),
            "serial": str(result.get("Serial", "")),
            "hostname": str(result.get("Hostname", result.get("Name", ""))),
            "uptime": str(result.get("Uptime", "")),
            "build_date": str(result.get("BuildDate", result.get("Date", ""))),
        }


class SystemLicenseParser(BaseParser):
    """Parse SYSTEM LICENSE SHOW responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse SYSTEM LICENSE SHOW response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized license entry dicts.
        """
        licenses: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            licenses.append(
                {
                    "module": str(raw.get("module", raw.get("name", ""))),
                    "status": str(raw.get("status", "")),
                    "expiry": str(raw.get("expiry", raw.get("expire", ""))),
                    "remaining_days": str(raw.get("remaining", "")),
                }
            )
        return licenses


class SystemHAParser(BaseParser):
    """Parse SYSTEM HA SHOW responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse SYSTEM HA SHOW response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            Normalized HA status dictionary.
        """
        result = cls._get_result_dict(data)
        return {
            "enabled": result.get("state", "off") != "off",
            "mode": str(result.get("mode", "")),
            "role": str(result.get("role", result.get("state", ""))),
            "peer_serial": str(result.get("peerserial", "")),
            "peer_version": str(result.get("peerversion", "")),
            "sync_state": str(result.get("sync", result.get("syncstate", ""))),
            "quality": str(result.get("quality", "")),
        }


class MonitorStatParser(BaseParser):
    """Parse MONITOR STAT responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse MONITOR STAT response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            Normalized monitoring statistics dictionary.
        """
        result = cls._get_result_dict(data)
        return {
            "cpu_percent": str(result.get("CPU", result.get("cpu", ""))),
            "memory_percent": str(result.get("Mem", result.get("mem", ""))),
            "connections": str(result.get("Connections", result.get("conn", ""))),
            "connection_rate": str(result.get("ConnRate", result.get("connrate", ""))),
            "host_count": str(result.get("Hosts", result.get("hosts", ""))),
        }


class UserParser(BaseParser):
    """Parse USER SHOW responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse USER SHOW response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            List of user dicts (passwords always excluded).
        """
        users: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            users.append(
                {
                    "name": str(raw.get("name", "")),
                    "group": str(raw.get("group", "")),
                    "status": str(raw.get("status", "")),
                    "auth_method": str(raw.get("auth", "")),
                    "comment": str(raw.get("comment", "")),
                }
            )
        return users


class AuthConfigParser(BaseParser):
    """Parse AUTH SHOW responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse AUTH SHOW response (credentials stripped).

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            Auth configuration dict with credentials removed.
        """
        result = cls._get_result_dict(data)
        safe: dict[str, Any] = {}
        sensitive_keys = {"password", "passwd", "secret", "bindpw", "token"}
        for k, v in result.items():
            if k.lower() in sensitive_keys:
                continue
            safe[k] = v
        return safe
