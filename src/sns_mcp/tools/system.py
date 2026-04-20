# SPDX-License-Identifier: Apache-2.0
"""System information and monitoring MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..client.command_executor import execute_command
from ..formatters.output import ToolResponse, make_ok, safe_tool_call
from ..parsers.system import (
    MonitorStatParser,
    SystemHAParser,
    SystemLicenseParser,
    SystemPropertyParser,
)

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager
    from ..config.models import AppConfig


def sns_system_info_get(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """Get general system information from the SNS device.

    Returns model name, firmware version, serial number, hostname, uptime.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_system_info_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SYSTEM PROPERTY", device_id)
        info = SystemPropertyParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, info, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_system_licenses_list(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """List all installed licenses and subscriptions with expiry dates.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_system_licenses_list"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SYSTEM LICENSE SHOW", device_id)
        licenses = SystemLicenseParser.parse(response.data, firmware)
        return make_ok(
            device_id,
            tool_name,
            licenses,
            firmware=firmware,
            count=len(licenses),
        )

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_system_ha_status_get(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """Get HA cluster status of the SNS device.

    Returns HA not configured message if the device is standalone.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_system_ha_status_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "SYSTEM HA SHOW", device_id)
        ha_info = SystemHAParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, ha_info, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_system_stats_get(
    manager: DeviceManager,
    device_id: str,
) -> str:
    """Get live system resource statistics.

    Returns CPU, memory, connections — live monitoring call.

    Args:
        manager: Device manager instance.
        device_id: ID of the target device.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_system_stats_get"

    def _execute() -> ToolResponse:
        client = manager.get_client(device_id)
        firmware = manager.get_firmware_version(device_id)
        response = execute_command(client, "MONITOR STAT", device_id)
        stats = MonitorStatParser.parse(response.data, firmware)
        return make_ok(device_id, tool_name, stats, firmware=firmware)

    result = safe_tool_call(device_id, tool_name, _execute)
    return result.to_json()


def sns_devices_list(
    config: AppConfig,
    manager: DeviceManager,
) -> str:
    """List all configured SNS devices (no credentials returned).

    Args:
        config: Application configuration.
        manager: Device manager instance.

    Returns:
        JSON string of ToolResponse.
    """
    tool_name = "sns_devices_list"
    devices = []

    for dev_id, dev_cfg in config.devices.items():
        devices.append(
            {
                "device_id": dev_id,
                "host": dev_cfg.host,
                "port": dev_cfg.port,
                "description": dev_cfg.description,
                "tags": dev_cfg.tags,
                "firmware_hint": dev_cfg.firmware_hint,
            }
        )

    result = make_ok(
        device_id="*",
        tool=tool_name,
        data=devices,
        count=len(devices),
    )
    return result.to_json()
