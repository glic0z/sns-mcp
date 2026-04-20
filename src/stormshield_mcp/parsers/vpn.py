# SPDX-License-Identifier: Apache-2.0
"""Parsers for IPsec and SSL VPN response data."""

from __future__ import annotations

from typing import Any

from .base import BaseParser


class VpnIpsecConfigParser(BaseParser):
    """Parse IPSECVPN SHOW CONFIG responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse IPSECVPN SHOW CONFIG response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized IPsec tunnel config dicts.
        """
        tunnels: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            tunnels.append(
                {
                    "name": str(raw.get("name", raw.get("peername", ""))),
                    "peer": str(raw.get("peer", raw.get("remote", ""))),
                    "local_gateway": str(raw.get("local", raw.get("localgw", ""))),
                    "remote_gateway": str(raw.get("remote", raw.get("remotegw", ""))),
                    "auth_method": str(raw.get("auth", raw.get("authmethod", ""))),
                    "ike_version": str(raw.get("ikeversion", raw.get("ike", ""))),
                    "encryption": str(raw.get("enc", raw.get("encryption", ""))),
                    "hash": str(raw.get("hash", "")),
                    "dh_group": str(raw.get("dhgroup", raw.get("dh", ""))),
                    "lifetime": str(raw.get("lifetime", "")),
                    "local_network": str(raw.get("localnet", raw.get("localsub", ""))),
                    "remote_network": str(raw.get("remotenet", raw.get("remotesub", ""))),
                    "enabled": raw.get("status", "on") == "on",
                    "comment": str(raw.get("comment", "")),
                }
            )
        return tunnels


class VpnIpsecSAParser(BaseParser):
    """Parse IPSECVPN SHOW SA responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse IPSECVPN SHOW SA response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            List of normalized SA status dicts.
        """
        sas: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            sas.append(
                {
                    "peer": str(raw.get("peer", raw.get("remote", ""))),
                    "state": str(raw.get("state", raw.get("status", ""))),
                    "local_network": str(raw.get("localnet", "")),
                    "remote_network": str(raw.get("remotenet", "")),
                    "encryption": str(raw.get("enc", "")),
                    "bytes_in": str(raw.get("bytesin", raw.get("inbytes", "0"))),
                    "bytes_out": str(raw.get("bytesout", raw.get("outbytes", "0"))),
                    "created": str(raw.get("created", "")),
                    "lifetime_remaining": str(raw.get("remaining", raw.get("lifetime", ""))),
                }
            )
        return sas


class VpnSslConfigParser(BaseParser):
    """Parse SSLVPN SHOW responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> dict[str, Any]:
        """Parse SSLVPN SHOW response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            Normalized SSL VPN configuration dictionary.
        """
        result = cls._get_result_dict(data)
        return {
            "enabled": result.get("status", "off") == "on",
            "interface": str(result.get("iface", "")),
            "port": str(result.get("port", "")),
            "protocol": str(result.get("proto", "")),
            "auth_method": str(result.get("auth", "")),
            "ip_pool": str(result.get("ippool", "")),
            "dns": str(result.get("dns", "")),
            "split_tunnel": result.get("splittunnel", "off") == "on",
        }


class VpnSslUsersParser(BaseParser):
    """Parse SSLVPN SHOW USERS responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse SSLVPN SHOW USERS response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version string.

        Returns:
            List of connected SSL VPN user dicts.
        """
        users: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            users.append(
                {
                    "username": str(raw.get("user", raw.get("username", ""))),
                    "assigned_ip": str(raw.get("ip", raw.get("addr", ""))),
                    "connected_since": str(raw.get("since", raw.get("connected", ""))),
                    "bytes_in": str(raw.get("bytesin", "0")),
                    "bytes_out": str(raw.get("bytesout", "0")),
                }
            )
        return users
