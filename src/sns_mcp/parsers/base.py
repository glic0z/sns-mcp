# SPDX-License-Identifier: Apache-2.0
"""Base parser class for SNS CLI response data."""

from __future__ import annotations

from typing import Any


class BaseParser:
    """Transform SNS SDK response.data into clean, consistent Python dicts.

    Parsers are stateless. They receive raw response data and return
    structured dicts. They never call the SNS API themselves.
    """

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
        firmware_version: str,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Parse SNS response data into structured output.

        Args:
            data: Raw response data from the SNS client.
            firmware_version: Major firmware version string ('3', '4', or '5').

        Returns:
            Parsed data as a list of dicts or a single dict.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError

    @classmethod
    def _safe_get(
        cls,
        d: dict[str, Any],
        *keys: str,
        default: Any = None,
    ) -> Any:
        """Safely traverse a nested dictionary.

        Args:
            d: The dictionary to traverse.
            *keys: Sequence of keys to follow.
            default: Default value if any key is missing.

        Returns:
            The value at the end of the key path, or the default.
        """
        current: Any = d
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
        return current

    @classmethod
    def _parse_list(cls, value: str | Any) -> list[str]:
        """Parse comma-separated or single values into a list.

        Args:
            value: A string with comma-separated values, or any other type.

        Returns:
            List of trimmed string values.
        """
        if not value:
            return []
        if not isinstance(value, str):
            return [str(value)]
        return [v.strip() for v in value.split(",") if v.strip()]

    @classmethod
    def _get_result_list(cls, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the Result section as a list of dicts.

        Handles both section_line (list) and section (single dict) formats.

        Args:
            data: Raw response data containing a 'Result' key.

        Returns:
            List of result dictionaries.
        """
        result = data.get("Result", [])
        if isinstance(result, list):
            return [r for r in result if isinstance(r, dict)]
        if isinstance(result, dict):
            return [result]
        return []

    @classmethod
    def _get_result_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Extract the Result section as a single dict.

        Args:
            data: Raw response data containing a 'Result' key.

        Returns:
            Result dictionary, or empty dict if not found.
        """
        result = data.get("Result", {})
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                return first
        return {}
