# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of stormshield-mcp
- Read-only MCP server for Stormshield SNS firewalls
- Support for SNS firmware versions 3.x, 4.x, and 5.x
- Multi-device support with device_id routing
- Capability probing system for automatic feature detection
- MCP tools for:
  - Filter rule listing and searching
  - NAT rule listing
  - Network object management (read-only)
  - Service object listing
  - Interface status monitoring
  - Routing table inspection
  - IPsec VPN configuration and SA status
  - SSL VPN configuration and connected users
  - System information, licenses, and HA status
  - Live monitoring (CPU, memory, connections)
  - User and authentication configuration
- STDIO and HTTP/SSE transport modes
- Structured JSON responses with ToolResponse envelope
- Input sanitization and command injection prevention
- Read-only enforcement with `assert_read_only` guard
- Credential scrubbing in all log output
- Pagination for large result sets
- Docker support with docker-compose
- One-click setup script
- Comprehensive unit tests with fixture data
- Full documentation (README, CONTRIBUTING, CONFIGURATION)
