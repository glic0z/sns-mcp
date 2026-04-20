# <div align="center">🛡️ sns-mcp</div>

<div align="center">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=24&pause=1000&color=2196F3&center=true&vCenter=true&width=600&lines=Read-only+MCP+server;For+Stormshield+SNS+firewalls;Secure.+Agentic.+Fast." alt="Typing SVG" />
  </a>
</div>

<div align="center">

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Build Status](https://img.shields.io/github/actions/workflow/status/glic0z/sns-mcp/ci.yml?branch=main)](https://github.com/glic0z/sns-mcp/actions)

> **Disclaimer:** This project is not affiliated with, endorsed by, or supported by Stormshield SAS. "Stormshield" and "SNS" are trademarks of Stormshield SAS.

</div>

---

## 🚀 What is this?

`sns-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives AI assistants read-only access to Stormshield SNS firewall data. Ask questions in natural language:

- *"Show me all filter rules allowing traffic to 10.0.0.0/8"*
- *"What IPsec tunnels are currently up?"*
- *"Which interfaces are in bridge mode?"*
- *"Find all NAT rules that translate source port 443"*

## Features

| Category | Tools |
|---|---|
| **Policy** | `sns_filter_rules_list`, `sns_nat_rules_list`, `sns_policy_slots_list` |
| **Objects** | `sns_network_objects_list`, `sns_network_object_get`, `sns_network_groups_list`, `sns_service_objects_list` |
| **Interfaces** | `sns_interfaces_list`, `sns_routing_table_get` |
| **VPN** | `sns_vpn_ipsec_config_list`, `sns_vpn_ipsec_status_list`, `sns_vpn_ssl_config_get`, `sns_vpn_ssl_users_list` |
| **System** | `sns_system_info_get`, `sns_system_licenses_list`, `sns_system_ha_status_get`, `sns_system_stats_get`, `sns_devices_list` |
| **Users** | `sns_users_list`, `sns_auth_config_get` |

## Supported Firmware

- **SNS 3.x** — Legacy support
- **SNS 4.x** — Full support
- **SNS 5.x** — Full support (including ZTNA, SD-WAN when licensed)

Works with all SNS models: SN210, SN310, SN510, SN710, SN910, SN2100, SN3100, SN6100, SNi series, and SNS virtual machines.

## 🔒 Read-Only Guarantee

**This tool never writes to your firewall.** Three layers of protection ensure this:

1. **No write tools** are registered in the MCP server
2. **A `assert_read_only` guard** blocks any write command at the executor level
3. **A dedicated read-only SNS account** (`api_monitor` in the `Monitor` group) is recommended

Credentials are never logged, never stored in code, and never returned in any tool response.

## Quick Start

### 1. Install

```bash
git clone https://github.com/glic0z/sns-mcp.git
cd sns-mcp
pip install -e .
```

### 2. Configure

```bash
# Edit config/config.yaml with your device details
nano config/config.yaml

# Set passwords via environment variables
export PARIS_FW_PASSWORD='your_password'
```

### 3. Run

```bash
# STDIO mode (for Claude Desktop)
sns-mcp --config config/config.yaml

# HTTP mode (for remote agents)
sns-mcp --config config/config.yaml --transport http
```

### 4. Docker

```bash
# Copy and edit config
cp config/config.example.yaml config/config.yaml
nano config/config.yaml

# Start
docker compose -f docker/docker-compose.yml up -d
```

### 5. Claude Desktop Integration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "stormshield": {
      "command": "sns-mcp",
      "args": ["--config", "/path/to/config.yaml"],
      "env": {
        "PARIS_FW_PASSWORD": "your_password_here"
      }
    }
  }
}
```

## Configuration

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full reference.

Key points:
- Config file: `config/config.yaml` (YAML)
- Passwords support `${ENV_VAR}` syntax for env var injection
- Environment variable overrides: `SNS_MCP_SERVER__PORT=9000`
- All string values are sanitized before use in CLI commands

## Development

```bash
make install     # Setup virtualenv + install
make test        # Run tests with coverage
make lint        # Ruff + mypy
make run         # Start STDIO server
make run-http    # Start HTTP server
make clean       # Remove build artifacts
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding tools, parsers, and tests.

## Contributors

* **[glicoz](https://github.com/glic0z)** - *Initial work & architecture*

Contributions, issues and feature requests are welcome! Feel free to check the [issues page](https://github.com/glic0z/sns-mcp/issues).

## License

[Apache 2.0](LICENSE)

---

> **Disclaimer:** This project is not affiliated with, endorsed by, or supported by Stormshield SAS. "Stormshield" and "SNS" are trademarks of Stormshield SAS. This is an independent community tool.
