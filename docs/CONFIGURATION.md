# Configuration Reference

## Config File Location

Default search paths:
1. `config/config.yaml`
2. `config.yaml`

Or specify with `--config /path/to/config.yaml`.

## Full Schema

### devices (required)

Map of device_id → device configuration. At least one device must be configured.

| Field | Type | Default | Description |
|---|---|---|---|
| `host` | string | *required* | IP address or hostname of the SNS device |
| `port` | integer | 443 | HTTPS port |
| `user` | string | *required* | Username for authentication |
| `password` | string | *required* | Password (supports `${ENV_VAR}` syntax) |
| `ssl_verify_host` | boolean | false | Verify SSL hostname |
| `ssl_verify_peer` | boolean | false | Verify SSL peer certificate |
| `cabundle` | string | null | Path to CA bundle PEM file |
| `timeout` | integer | 30 | Command timeout in seconds (5-300) |
| `firmware_hint` | string | null | Skip auto-detect: "3", "4", or "5" |
| `description` | string | "" | Human-readable description |
| `tags` | list[string] | [] | Tags for filtering/grouping |

### server

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | sns-mcp | Server name |
| `version` | string | 0.1.0 | Server version |
| `host` | string | 127.0.0.1 | HTTP bind address |
| `port` | integer | 8765 | HTTP port |
| `path` | string | /mcp | HTTP endpoint path |

> ⚠️ **Never** bind to `0.0.0.0` without a reverse proxy with TLS.

### capabilities

| Field | Type | Default | Description |
|---|---|---|---|
| `probe_on_start` | boolean | true | Test capabilities at startup |
| `probe_timeout` | integer | 10 | Timeout per probe command |

### logging

| Field | Type | Default | Description |
|---|---|---|---|
| `level` | string | INFO | DEBUG, INFO, WARNING, ERROR |
| `format` | string | json | "json" or "text" |
| `file` | string | null | Log file path (null = stderr) |

## Environment Variable Overrides

Any config value can be overridden:

```bash
SNS_MCP_SERVER__PORT=9000
SNS_MCP_LOGGING__LEVEL=DEBUG
SNS_MCP_DEVICE__MYFW__HOST=10.0.0.1
```

## Password Environment Variables

Use `${VAR_NAME}` in config.yaml to inject env vars:

```yaml
password: "${MY_FW_PASSWORD}"
```

## Security Recommendations

1. **Create a read-only SNS user**: `USER ADD name=api_monitor group=Monitor`
2. **Set file permissions**: `chmod 600 config/config.yaml`
3. **Use environment variables** for passwords, never hardcode them
4. **Use SSL verification** in production with a proper CA bundle
5. **Use a reverse proxy** with TLS when running in HTTP mode
