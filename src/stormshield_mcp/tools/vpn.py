# SPDX-License-Identifier: Apache-2.0
"""VPN MCP tools (IPsec and SSL VPN)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..client.command_executor import execute_command, sanitize_input
from ..formatters.output import ToolResponse, make_ok, paginate, safe_tool_call
from ..parsers.vpn import (
    VpnIpsecConfigParser,
    VpnIpsecSAParser,
    VpnSslConfigParser,
    VpnSslUsersParser,
)

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager


def sns_vpn_ipsec_config_list(
    manager: DeviceManager,
    device_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all IPsec VPN tunnel configurations (phase1 + phase2).

    Does NOT return live tunnel status — use sns_vpn_ipsec_status_list.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        search: Optional search on peer name or IP.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_vpn_ipsec_config_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "IPSECVPN SHOW CONFIG", device_id)
        tunnels = VpnIpsecConfigParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            lower = sanitized.lower()
            tunnels = [t for t in tunnels if any(lower in str(v).lower() for v in t.values())]

        page_items, pg, ps, tp = paginate(tunnels, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(tunnels),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_vpn_ipsec_status_list(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """List the live status of all IPsec Security Associations.

    This is a live monitoring call — results change in real time.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_vpn_ipsec_status_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "IPSECVPN SHOW SA", device_id)
        sas = VpnIpsecSAParser.parse(response.data, firmware)
        return make_ok(
            device_id,
            tool_name,
            sas,
            firmware=firmware,
            count=len(sas),
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_vpn_ssl_config_get(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """Get the SSL VPN configuration of the SNS device.

    Does NOT return connected user sessions.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_vpn_ssl_config_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SSLVPN SHOW", device_id)
        config = VpnSslConfigParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, config, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_vpn_ssl_users_list(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """List users currently connected via SSL VPN.

    This is a live monitoring call.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_vpn_ssl_users_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SSLVPN SHOW USERS", device_id)
        users = VpnSslUsersParser.parse(response.data, firmware)
        return make_ok(
            device_id,
            tool_name,
            users,
            firmware=firmware,
            count=len(users),
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
