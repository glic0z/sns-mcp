# Adding a New Tool

This guide walks through adding a new MCP tool to sns-mcp.

## Prerequisites

- Know the SNS CLI command you want to wrap
- Know the response format (run it on a test device or check the spec)
- Have a fixture file with realistic output

## Step-by-Step

### 1. Create or Update the Parser

In `src/sns_mcp/parsers/`, create or update the appropriate parser:

```python
# parsers/your_module.py
from .base import BaseParser

class YourParser(BaseParser):
    @classmethod
    def parse(cls, data, firmware_version):
        results = []
        for raw in cls._get_result_list(data):
            results.append({
                "field1": str(raw.get("field1", "")),
                "field2": str(raw.get("field2", "")),
            })
        return results
```

### 2. Create the Tool Function

In `src/sns_mcp/tools/`, add the tool function:

```python
def sns_your_noun_verb(manager, device_id, **kwargs):
    tool_name = "sns_your_noun_verb"

    def _execute():
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "YOUR COMMAND", device_id)
        parsed = YourParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, parsed, firmware=firmware, count=len(parsed))

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
```

### 3. Register in server.py

Add the tool to `_register_all_tools()` in `src/sns_mcp/server.py`:

```python
@mcp.tool()
def sns_your_noun_verb(device_id: str) -> str:
    """Description for the LLM."""
    return your_module.sns_your_noun_verb(manager, device_id)
```

### 4. Add Capability Probe (if needed)

If the command may not be available on all devices, add a probe in
`src/sns_mcp/capabilities/probe.py`:

```python
CAPABILITY_PROBES["your_feature"] = "YOUR COMMAND"
```

### 5. Create Fixtures and Tests

Add fixture files in `tests/fixtures/` and tests in `tests/unit/`.

### 6. Naming Convention

- Tool name: `sns_<noun>_<verb>` (e.g., `sns_filter_rules_list`)
- Always snake_case
- Always prefixed with `sns_`
