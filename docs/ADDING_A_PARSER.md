# Adding a New Parser

Parsers transform raw SNS CLI response data into clean Python dicts.

## Parser Rules

1. **Inherit from `BaseParser`** — use `_get_result_list()` and `_get_result_dict()`
2. **Handle both formats** — `section` (single dict) and `section_line` (list of dicts)
3. **Handle all firmware versions** — SNS 3.x, 4.x, and 5.x may use different field names
4. **Never return credentials** — strip password, passwd, secret, token, bindpw fields
5. **Be defensive** — use `.get()` with defaults, never assume a field exists
6. **Use `str()` casts** — ensure all values are strings for JSON serialization

## Template

```python
# SPDX-License-Identifier: Apache-2.0
"""Parser for YOUR_COMMAND response data."""
from __future__ import annotations
from typing import Any
from .base import BaseParser

class YourParser(BaseParser):
    """Parse YOUR_COMMAND responses."""

    @classmethod
    def parse(cls, data: dict[str, Any], firmware_version: str) -> list[dict[str, Any]]:
        """Parse YOUR_COMMAND response.

        Args:
            data: Raw response data.
            firmware_version: Major firmware version ('3', '4', or '5').

        Returns:
            List of normalized dictionaries.
        """
        results: list[dict[str, Any]] = []
        for raw in cls._get_result_list(data):
            results.append({
                "name": str(raw.get("name", "")),
                # SNS 5.x uses "newfield", 4.x uses "oldfield"
                "field": str(raw.get("newfield", raw.get("oldfield", ""))),
            })
        return results
```

## Testing

Create fixture files in `tests/fixtures/` and test with:

```python
def test_parse_your_data():
    response = load_fixture("your_command.txt")
    result = YourParser.parse(response.data, "4")
    assert len(result) == expected_count
    assert result[0]["name"] == "expected_name"
```
