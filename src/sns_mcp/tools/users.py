# SPDX-License-Identifier: Apache-2.0
"""User and authentication MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..client.command_executor import execute_command, sanitize_input
from ..formatters.output import ToolResponse, make_ok, paginate, safe_tool_call
from ..parsers.system import AuthConfigParser, UserParser

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager


def sns_users_list(
    manager: DeviceManager,
    device_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List local user accounts defined on the SNS device.

    Never returns passwords or password hashes.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        search: Optional text search on username or group.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_users_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "USER SHOW", device_id)
        users = UserParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            lower = sanitized.lower()
            users = [u for u in users if any(lower in str(v).lower() for v in u.values())]

        page_items, pg, ps, tp = paginate(users, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(users),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_auth_config_get(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """Get authentication method configuration.

    Never returns bind passwords or service account credentials.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_auth_config_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "AUTH SHOW", device_id)
        auth = AuthConfigParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, auth, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
