# SPDX-License-Identifier: Apache-2.0
"""Parser for Stormshield SNS log files."""

from __future__ import annotations

import re
from typing import Any


def parse_log_lines(raw_data: str | list[str] | dict[str, Any]) -> list[dict[str, str]]:
    """Parse raw log lines into structured dictionaries.

    SNS logs typically come as a list of strings, each containing key=value pairs.
    Example line: tz="UTC" date="2023-10-10 10:00:00" action="pass" src="1.2.3.4"

    Args:
        raw_data: The raw log data returned by the SNS client.

    Returns:
        List of parsed log entries.
    """
    if isinstance(raw_data, dict):
        # Depending on how SSLClient wraps it, the lines might be inside a list
        if "Result" in raw_data:
            return parse_log_lines(raw_data["Result"])
        return []

    lines: list[str] = []
    if isinstance(raw_data, str):
        lines = raw_data.strip().splitlines()
    elif isinstance(raw_data, list):
        lines = [str(x) for x in raw_data]

    parsed_logs: list[dict[str, str]] = []

    # Regex to match key=value or key="value" (handles escaped quotes inside)
    # Matches: key="value" OR key='value' OR key=value
    kv_pattern = re.compile(r'([a-zA-Z0-9_]+)=("([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'|([^\s]+))')

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        entry: dict[str, str] = {}
        for match in kv_pattern.finditer(line):
            key = match.group(1)
            # group 3 is double-quoted value, group 4 is single-quoted, group 5 is unquoted
            val = match.group(3) if match.group(3) is not None else (
                  match.group(4) if match.group(4) is not None else match.group(5))
            entry[key] = val or ""

        if entry:
            parsed_logs.append(entry)

    return parsed_logs
