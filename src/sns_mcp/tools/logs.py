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
    """Fetch recent log lines from a specific firewall log file."""
    tool_name = "sns_logs_read"
    lines = min(max(1, lines), 1000)
    command = f'LOG DOWNLIMIT file="{log_type}" line="{lines}"'

    def _execute() -> Any:
        from ..client.command_executor import execute_command
        from ..formatters.output import make_ok
        
        client = manager.get_client(device_id)
        response = execute_command(client, command, device_id)
        
        # Parse the raw data into dictionaries
        parsed_data = parse_log_lines(response.data)
        
        return make_ok(
            device_id,
            tool_name,
            parsed_data,
        )

    from ..formatters.output import safe_tool_call
    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_logs_search(
    manager: DeviceManager,
    device_id: str,
    log_type: str = "filter",
    query: str = "",
    lines: int = 100,
) -> str:
    """Search for a specific keyword in a firewall log file."""
    tool_name = "sns_logs_search"
    lines = min(max(1, lines), 1000)
    
    if not query:
        return sns_logs_read(manager, device_id, log_type, lines)

    command = f'LOG SEARCH file="{log_type}" search="{query}" line="{lines}"'

    def _execute() -> Any:
        from ..client.command_executor import execute_command
        from ..formatters.output import make_ok
        
        client = manager.get_client(device_id)
        response = execute_command(client, command, device_id)
        parsed_data = parse_log_lines(response.data)
        
        return make_ok(
            device_id,
            tool_name,
            parsed_data,
        )

    from ..formatters.output import safe_tool_call
    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
