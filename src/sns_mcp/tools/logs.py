# SPDX-License-Identifier: Apache-2.0
"""Tools for reading and searching firewall logs."""

from __future__ import annotations

import json
from typing import Any

from ..client.device_manager import DeviceManager
from ..formatters.output import format_list_output
from ..parsers.logs import parse_log_lines


def sns_logs_read(
    manager: DeviceManager,
    device_id: str,
    log_type: str = "filter",
    lines: int = 100,
) -> str:
    """Fetch recent log lines from a specific firewall log file.

    Args:
        manager: The device manager instance.
        device_id: ID of the target device.
        log_type: The log file to read (e.g., 'filter', 'alarm', 'system', 'auth').
        lines: Number of recent lines to fetch (max 1000).

    Returns:
        JSON string containing the parsed log entries.
    """
    lines = min(max(1, lines), 1000)

    # Use LOG DOWNLIMIT to get the most recent X lines from the specified file
    command = f'LOG DOWNLIMIT file="{log_type}" line="{lines}"'

    def _execute(client: Any) -> Any:
        return client.send_command(command)

    try:
        response = manager.execute(device_id, _execute)
        
        # Parse the raw data into dictionaries
        parsed_data = parse_log_lines(response.data)
        
        return format_list_output(
            parsed_data,
            title=f"Recent '{log_type}' Logs",
            device_id=device_id,
        )
    except Exception as exc:
        return json.dumps(
            {"error": f"Failed to read logs: {exc}"},
            indent=2,
        )


def sns_logs_search(
    manager: DeviceManager,
    device_id: str,
    log_type: str = "filter",
    query: str = "",
    lines: int = 100,
) -> str:
    """Search for a specific keyword in a firewall log file.

    Args:
        manager: The device manager instance.
        device_id: ID of the target device.
        log_type: The log file to search (e.g., 'filter', 'alarm', 'system', 'auth').
        query: The string or IP address to search for.
        lines: Maximum number of lines to return (max 1000).

    Returns:
        JSON string containing the matched log entries.
    """
    lines = min(max(1, lines), 1000)
    
    if not query:
        return sns_logs_read(manager, device_id, log_type, lines)

    # The SNS CLI supports LOG SEARCH. 
    # Usually `LOG SEARCH file="filter" search="1.1.1.1" line="100"`
    command = f'LOG SEARCH file="{log_type}" search="{query}" line="{lines}"'

    def _execute(client: Any) -> Any:
        return client.send_command(command)

    try:
        response = manager.execute(device_id, _execute)
        parsed_data = parse_log_lines(response.data)
        
        return format_list_output(
            parsed_data,
            title=f"Search Results for '{query}' in '{log_type}' Logs",
            device_id=device_id,
        )
    except Exception as exc:
        return json.dumps(
            {"error": f"Failed to search logs: {exc}"},
            indent=2,
        )
