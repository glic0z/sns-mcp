# SPDX-License-Identifier: Apache-2.0
"""Interface and routing MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..client.command_executor import execute_command, sanitize_input
from ..formatters.output import ToolResponse, make_ok, paginate, safe_tool_call
from ..parsers.interfaces import InterfaceParser
from ..parsers.routing import RoutingParser

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager


def sns_interfaces_list(
    manager: DeviceManager,
    device_id: str,
    status_filter: str = "all",
) -> str:
    """List all network interfaces with their current status.

    Returns physical interfaces, VLANs, bridges, LACP, loopback and tunnel.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        status_filter: Filter by link state (up/down/all).

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_interfaces_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "INTERFACE SHOW", device_id)
        ifaces = InterfaceParser.parse(response.data, firmware)

        if status_filter != "all":
            ifaces = [i for i in ifaces if i.get("status") == status_filter]

        return make_ok(
            device_id,
            tool_name,
            ifaces,
            firmware=firmware,
            count=len(ifaces),
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_routing_table_get(
    manager: DeviceManager,
    device_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """Get the full routing table from the SNS device.

    Returns all routes (static, dynamic, connected, policy-based).

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        search: Optional search on destination or gateway.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_routing_table_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "ROUTE SHOW", device_id)
        routes = RoutingParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            lower = sanitized.lower()
            routes = [r for r in routes if any(lower in str(v).lower() for v in r.values())]

        page_items, pg, ps, tp = paginate(routes, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(routes),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
