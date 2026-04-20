# SPDX-License-Identifier: Apache-2.0
"""Consistent MCP response formatting with ToolResponse envelope."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("stormshield_mcp.formatters")


@dataclass
class ToolResponse:
    """Standard response envelope for all MCP tools.

    Attributes:
        device_id: ID of the device queried.
        tool: Name of the MCP tool that produced this response.
        status: Result status (ok, error, capability_unavailable, not_found).
        data: The actual result data.
        count: Number of items for list results.
        firmware: Firmware version of the queried device.
        capability_note: Explanation when status is not 'ok'.
        timestamp: ISO 8601 timestamp of when the response was generated.
        page: Current page number for paginated results.
        page_size: Items per page for paginated results.
        total_pages: Total number of pages for paginated results.
    """

    device_id: str
    tool: str
    status: str  # "ok" | "error" | "capability_unavailable" | "not_found"
    data: Any
    count: int | None = None
    firmware: str | None = None
    capability_note: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None

    def to_json(self) -> str:
        """Serialize the response to a JSON string.

        Returns:
            JSON string representation of this response.
        """
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def make_ok(
    device_id: str,
    tool: str,
    data: Any,
    firmware: str | None = None,
    count: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
    total_pages: int | None = None,
) -> ToolResponse:
    """Create a successful ToolResponse.

    Args:
        device_id: Device identifier.
        tool: Tool name.
        data: Result data.
        firmware: Firmware version.
        count: Item count for list results.
        page: Current page.
        page_size: Page size.
        total_pages: Total pages.

    Returns:
        ToolResponse with status='ok'.
    """
    return ToolResponse(
        device_id=device_id,
        tool=tool,
        status="ok",
        data=data,
        count=count,
        firmware=firmware,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def make_error(
    device_id: str,
    tool: str,
    message: str,
) -> ToolResponse:
    """Create an error ToolResponse.

    Args:
        device_id: Device identifier.
        tool: Tool name.
        message: Error description.

    Returns:
        ToolResponse with status='error'.
    """
    return ToolResponse(
        device_id=device_id,
        tool=tool,
        status="error",
        data=None,
        capability_note=message,
    )


def make_capability_unavailable(
    device_id: str,
    tool: str,
    message: str,
) -> ToolResponse:
    """Create a capability_unavailable ToolResponse.

    Args:
        device_id: Device identifier.
        tool: Tool name.
        message: Explanation of why the capability is unavailable.

    Returns:
        ToolResponse with status='capability_unavailable'.
    """
    return ToolResponse(
        device_id=device_id,
        tool=tool,
        status="capability_unavailable",
        data=None,
        capability_note=message,
    )


def paginate(
    items: list[Any],
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[Any], int, int, int]:
    """Paginate a list of items.

    Args:
        items: Full list of items to paginate.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (page_items, page, page_size, total_pages).
    """
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], page, page_size, total_pages


def safe_tool_call(
    device_id: str,
    tool_name: str,
    fn: Callable[[], ToolResponse],
) -> ToolResponse:
    """Execute a tool function with comprehensive error handling.

    Catches all exceptions and converts them to structured ToolResponse
    objects. Never raises to the MCP caller.

    Args:
        device_id: Device identifier.
        tool_name: Name of the tool being called.
        fn: Callable that produces the ToolResponse.

    Returns:
        ToolResponse (either from fn or an error envelope).
    """
    from ..client.command_executor import CapabilityUnavailableError
    from ..client.device_manager import (
        AuthenticationError,
        DeviceNotFoundError,
        DeviceUnreachableError,
    )

    try:
        return fn()
    except DeviceNotFoundError:
        return make_error(
            device_id,
            tool_name,
            f"Device '{device_id}' is not configured. "
            "Use sns_devices_list to see available devices.",
        )
    except DeviceUnreachableError as e:
        return make_error(
            device_id,
            tool_name,
            f"Cannot reach device '{device_id}': {e}",
        )
    except CapabilityUnavailableError as e:
        return make_capability_unavailable(
            device_id,
            tool_name,
            e.reason or f"Feature '{e.capability}' not available.",
        )
    except AuthenticationError:
        return make_error(
            device_id,
            tool_name,
            "Authentication failed. Check credentials in config.",
        )
    except Exception as e:
        logger.exception("Unexpected error in %s for %s", tool_name, device_id)
        return make_error(
            device_id,
            tool_name,
            f"Unexpected error: {type(e).__name__}: {e}",
        )
