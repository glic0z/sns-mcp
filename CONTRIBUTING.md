# Contributing to stormshield-mcp

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone and setup
git clone https://github.com/glic0z/stormshield-mcp.git
cd stormshield-mcp
pip install -e ".[dev]"  # One-click setup
# OR manually:
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Code Style

- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type checker**: `mypy --strict`
- **Every function** must have type hints and a docstring
- **SPDX header** on every source file: `# SPDX-License-Identifier: Apache-2.0`
- Run `make lint` before submitting a PR

## How to Add a New Tool

1. **Identify the SNS CLI command** (see `docs/ADDING_A_TOOL.md`)
2. **Create or update a parser** in `src/stormshield_mcp/parsers/`
3. **Create the tool function** in the appropriate `src/stormshield_mcp/tools/` module
4. **Register the tool** in `src/stormshield_mcp/server.py` → `_register_all_tools()`
5. **Add capability probe** if needed in `src/stormshield_mcp/capabilities/probe.py`
6. **Create fixture files** in `tests/fixtures/`
7. **Write unit tests** for both the parser and the tool
8. **Update documentation** in README.md

### Tool Implementation Pattern

```python
def sns_<noun>_<verb>(
    manager: DeviceManager,
    device_id: str,
    # ... other params
) -> str:
    tool_name = "sns_<noun>_<verb>"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "YOUR COMMAND", device_id)
        parsed = YourParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, parsed, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()
```

## How to Add a New Parser

See `docs/ADDING_A_PARSER.md` for the full guide. Key points:

1. Inherit from `BaseParser`
2. Implement the `parse()` classmethod
3. Handle both `section` and `section_line` response formats
4. Handle SNS 3.x, 4.x, and 5.x field name differences
5. Never return credential/password fields
6. Write tests with fixture data for all firmware versions

## Test Fixture Format

Fixtures simulate real SNS CLI output. Format:

```
101 code=00a01000 msg="Begin" format="section_line"
[Result]
key1=value1 key2=value2 key3="quoted value"
key1=value1 key2=value2 key3="another value"
100 code=00a00100 msg="Ok"
```

## PR Checklist

Before submitting a pull request:

- [ ] `make lint` passes with zero errors
- [ ] `make test` passes with ≥ 80% coverage
- [ ] All new code has type hints and docstrings
- [ ] All new source files have the SPDX header
- [ ] New tools follow the naming convention: `sns_<noun>_<verb>`
- [ ] New tools return `ToolResponse` JSON, never raw text
- [ ] New tools handle errors via `safe_tool_call`, never raise
- [ ] No credentials appear in any output or log
- [ ] Fixture files are realistic and cover edge cases
- [ ] Documentation updated (README, CHANGELOG)

## Reporting Issues

Use the GitHub issue templates:
- **Bug Report**: Include firmware version, tool name, and error output
- **Feature Request**: Describe the SNS command and use case

## Code of Conduct

Be respectful and constructive. We're all here to build useful tools.
