# SPDX-License-Identifier: Apache-2.0
"""Startup capability detection for SNS devices."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.device_manager import DeviceManager
    from ..client.sns_client import SNSClient
    from ..config.models import AppConfig

logger = logging.getLogger("sns_mcp.capabilities.probe")

# Maps capability keys to the SNS CLI command used to probe them.
CAPABILITY_PROBES: dict[str, str] = {
    "filter": "FILTER SLOT SHOW",
    "nat": "NAT SLOT SHOW",
    "objects": "OBJECT SHOW type=host",
    "routing": "ROUTE SHOW",
    "interfaces": "INTERFACE SHOW",
    "vpn_ipsec": "IPSECVPN SHOW CONFIG",
    "vpn_ssl": "SSLVPN SHOW",
    "users": "USER SHOW",
    "system": "SYSTEM PROPERTY",
    "ha": "SYSTEM HA SHOW",
    "monitor": "MONITOR STAT",
    "url_filter": "URLFILTER SHOW",
    "app_inspect": "APPINSPECT SHOW",
    "ztna": "ZTNA SHOW",
    "sdwan": "SDWAN SHOW",
    "ntp": "NTP SHOW",
    "dns": "DNS SHOW",
    "snmp": "SNMP SHOW",
    "global_policy": "FILTER GLOBAL SHOW",
    "logs": 'LOG INFO file="filter"',
}


def probe_device(device_id: str, client: SNSClient) -> dict[str, bool]:
    """Run all capability probes against a single device.

    Tests each command from CAPABILITY_PROBES and records whether
    it succeeds. Never raises — failures are logged and recorded as False.

    Args:
        device_id: Identifier of the device being probed.
        client: Connected SNS client for the device.

    Returns:
        Dictionary mapping capability keys to availability booleans.
    """
    results: dict[str, bool] = {}
    ok_codes = {"00a00100", "00a01000"}

    for capability, command in CAPABILITY_PROBES.items():
        try:
            response = client.send_command(command)
            results[capability] = response.ret in ok_codes
            if results[capability]:
                logger.debug("[%s] Capability '%s': available", device_id, capability)
            else:
                logger.debug(
                    "[%s] Capability '%s': unavailable (code=%s)",
                    device_id,
                    capability,
                    response.ret,
                )
        except Exception as exc:
            logger.debug("[%s] Probe '%s' failed: %s", device_id, capability, exc)
            results[capability] = False

    available_count = sum(1 for v in results.values() if v)
    logger.info(
        "[%s] Capability probe complete: %d/%d available",
        device_id,
        available_count,
        len(results),
    )
    return results


def probe_all_devices(
    manager: DeviceManager,
    config: AppConfig,
) -> dict[str, dict[str, bool]]:
    """Run capability probes on all configured devices.

    Args:
        manager: Device manager with connection pool.
        config: Application configuration.

    Returns:
        Dictionary mapping device IDs to their capability dictionaries.
    """
    all_capabilities: dict[str, dict[str, bool]] = {}

    for device_id in config.devices:
        try:
            client = manager.get_client(device_id)
            all_capabilities[device_id] = probe_device(device_id, client)
        except Exception as exc:
            logger.warning("[%s] Skipping probe — device unreachable: %s", device_id, exc)
            # Mark all capabilities as unavailable
            all_capabilities[device_id] = dict.fromkeys(CAPABILITY_PROBES, False)

    return all_capabilities
