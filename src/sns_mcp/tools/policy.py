# SPDX-License-Identifier: Apache-2.0
"""Filter and NAT rule MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.command_executor import execute_command, sanitize_input
from ..formatters.output import (
    ToolResponse,
    make_ok,
    paginate,
    safe_tool_call,
)
from ..parsers.filter_rules import FilterRuleParser
from ..parsers.nat_rules import NatRuleParser

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager


def _search_filter(items: list[dict[str, Any]], search: str) -> list[dict[str, Any]]:
    """Filter items by a search term across all string fields."""
    lower = search.lower()
    results: list[dict[str, Any]] = []
    for item in items:
        if _item_matches(item, lower):
            results.append(item)
    return results


def _item_matches(item: dict[str, Any], search: str) -> bool:
    """Check if any field in a dict contains the search string."""
    for v in item.values():
        if isinstance(v, str) and search in v.lower():
            return True
        if isinstance(v, dict) and _item_matches(v, search):
            return True
        if isinstance(v, list):
            for elem in v:
                if isinstance(elem, str) and search in elem.lower():
                    return True
    return False


def sns_filter_rules_list(
    manager: DeviceManager,
    device_id: str,
    slot: int | None = None,
    action_filter: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all filter (firewall) rules on the specified SNS device.

    Returns rules from the active policy slot by default, or a specific slot
    if 'slot' is provided. Each rule includes: rule name, action, source,
    destination, service/port, schedule, inspection profile, and status.

    Does NOT return NAT rules — use sns_nat_rules_list for those.
    Does NOT modify any configuration.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device as declared in config.yaml.
        slot: Policy slot number (1-10). If None, uses the active slot.
        action_filter: Optional filter by rule action.
        search: Optional text search across all rule fields.
        page: Page number (1-indexed).
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_filter_rules_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)

        cmd = "FILTER SHOW"
        if slot is not None:
            cmd = f"FILTER SLOT slot={slot} SHOW"

        response = execute_command(client, cmd, device_id)
        rules = FilterRuleParser.parse(response.data, firmware)

        if action_filter:
            rules = [r for r in rules if r.get("action") == action_filter]

        if search:
            sanitized = sanitize_input(search, "search")
            rules = _search_filter(rules, sanitized)

        page_items, pg, ps, tp = paginate(rules, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(rules),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_nat_rules_list(
    manager: DeviceManager,
    device_id: str,
    slot: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> str:
    """List all NAT rules on the specified SNS device.

    Returns all NAT rules from the active slot or a specific slot.
    Does NOT return filter rules — use sns_filter_rules_list for those.
    Does NOT modify any configuration.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.
        slot: Policy slot number (1-10).
        search: Optional text search across all rule fields.
        page: Page number.
        page_size: Items per page.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_nat_rules_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)

        cmd = "NAT SHOW"
        if slot is not None:
            cmd = f"NAT SLOT slot={slot} SHOW"

        response = execute_command(client, cmd, device_id)
        rules = NatRuleParser.parse(response.data, firmware)

        if search:
            sanitized = sanitize_input(search, "search")
            rules = _search_filter(rules, sanitized)

        page_items, pg, ps, tp = paginate(rules, page, page_size)
        return make_ok(
            device_id,
            tool_name,
            page_items,
            firmware=firmware,
            count=len(rules),
            page=pg,
            page_size=ps,
            total_pages=tp,
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_policy_slots_list(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """List all policy slots and identify the currently active slot.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_policy_slots_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "FILTER SLOT SHOW", device_id)
        result = response.data.get("Result", [])
        data: list[dict[str, Any]] | dict[str, Any]
        if isinstance(result, list):
            data = result
        elif isinstance(result, dict):
            data = [result]
        else:
            data = []
        count = len(data) if isinstance(data, list) else 1
        return make_ok(device_id, tool_name, data, firmware=firmware, count=count)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
