# SPDX-License-Identifier: Apache-2.0
"""Network and service object MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.command_executor import execute_command, sanitize_input
from ..formatters.output import (
    ToolResponse,
    make_ok,
    paginate,
    safe_tool_call,
)
from ..parsers.objects import ObjectGroupParser, ObjectParser, ServiceParser

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager


def _search_filter(items: list[dict[str, Any]], search: str) -> list[dict[str, Any]]:
    """Filter items by search term across all string fields."""
    lower = search.lower()
    return [
        item
        for item in items
        if any(isinstance(v, str) and lower in v.lower() for v in item.values())
    ]


def sns_network_objects_list(
    manager: DeviceManager,
    device_id: str,
    object_type: str = "all",
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all network objects defined on the SNS device.

    Returns hosts, networks, IP ranges, and FQDN objects.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        object_type: Filter by type (host/network/range/fqdn/all).
        search: Optional text search on name, IP, or comment.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_network_objects_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)

        if object_type != "all":
            sanitized_type = sanitize_input(object_type, "object_type")
            cmd = f"OBJECT TYPE={sanitized_type} SHOW"
        else:
            cmd = "OBJECT SHOW"

        response = execute_command(client, cmd, device_id)
        objects = ObjectParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            objects = _search_filter(objects, sanitized)

        page_items, pg, ps, tp = paginate(objects, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(objects),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_network_object_get(
    manager: DeviceManager,
    device_id: str,
    name: str,
) -> str:
    """Get the full details of a single named network object.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        name: Exact name of the network object.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_network_object_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        sanitized_name = sanitize_input(name, "name")
        cmd = f"OBJECT SHOW name={sanitized_name}"
        response = execute_command(client, cmd, device_id)
        objects = ObjectParser.parse(response.data, firmware)
        data = objects[0] if objects else None
        return make_ok(device_id, tool_name, data, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_network_groups_list(
    manager: DeviceManager,
    device_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all network object groups and their members.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        search: Optional text search on group name or member names.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_network_groups_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "OBJECT GROUP SHOW", device_id)
        groups = ObjectGroupParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            groups = _search_filter(groups, sanitized)

        page_items, pg, ps, tp = paginate(groups, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(groups),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_service_objects_list(
    manager: DeviceManager,
    device_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all service (port/protocol) objects.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        search: Optional text search on name or port.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_service_objects_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SERVICE SHOW", device_id)
        services = ServiceParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            services = _search_filter(services, sanitized)

        page_items, pg, ps, tp = paginate(services, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(services),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
