# SPDX-License-Identifier: Apache-2.0
"""Multi-device connection pool and health checking."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .sns_client import SNSClient, SNSResponse

if TYPE_CHECKING:
    from ..config.models import AppConfig

logger = logging.getLogger("sns_mcp.client.device_manager")


class DeviceNotFoundError(Exception):
    """Raised when a device_id is not in the configuration."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Device '{device_id}' is not configured")


class DeviceUnreachableError(Exception):
    """Raised when a device cannot be reached."""

    def __init__(self, device_id: str, reason: str = "") -> None:
        self.device_id = device_id
        self.reason = reason
        super().__init__(f"Cannot reach device '{device_id}': {reason}")


class AuthenticationError(Exception):
    """Raised when authentication to a device fails."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Authentication failed for device '{device_id}'")


class DeviceManager:
    """Manages connections to multiple SNS devices.

    Maintains a pool of SNSClient instances, one per configured device.
    Handles connection creation, health checking, and reconnection.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize the device manager.

        Args:
            config: Application configuration containing device definitions.
        """
        self._clients: dict[str, SNSClient] = {}
        self._config = config
        self._firmware_cache: dict[str, str] = {}

    def get_device_ids(self) -> list[str]:
        """Return all configured device IDs.

        Returns:
            List of device ID strings.
        """
        return list(self._config.devices.keys())

    def get_client(self, device_id: str) -> SNSClient:
        """Get or create an SNS client for the specified device.

        Args:
            device_id: The device identifier from the configuration.

        Returns:
            Connected SNSClient instance.

        Raises:
            DeviceNotFoundError: If device_id is not in the configuration.
            DeviceUnreachableError: If the device cannot be reached.
        """
        if device_id not in self._config.devices:
            raise DeviceNotFoundError(device_id)

        # Return cached client if available and healthy
        if device_id in self._clients:
            client = self._clients[device_id]
            if self._is_healthy(client):
                return client
            # Stale client — disconnect and reconnect
            logger.info("Reconnecting to device '%s'", device_id)
            client.disconnect()
            del self._clients[device_id]

        # Create new client
        device_cfg = self._config.devices[device_id]
        client = SNSClient(
            host=device_cfg.host,
            port=device_cfg.port,
            user=device_cfg.user,
            password=device_cfg.password,
            sslverifyhost=device_cfg.ssl_verify_host,
            sslverifypeer=device_cfg.ssl_verify_peer,
            cabundle=device_cfg.cabundle,
            timeout=device_cfg.timeout,
        )

        if not client.connect():
            raise DeviceUnreachableError(
                device_id, f"Failed to connect to {device_cfg.host}:{device_cfg.port}"
            )

        self._clients[device_id] = client
        return client

    def _is_healthy(self, client: SNSClient) -> bool:
        """Check if an SNS client connection is still healthy.

        Args:
            client: The SNS client to check.

        Returns:
            True if the client can communicate with the device.
        """
        try:
            response: SNSResponse = client.send_command("SYSTEM PROPERTY")
            return response.is_ok
        except Exception:
            return False

    def get_firmware_version(self, device_id: str) -> str:
        """Get the firmware major version for a device.

        Uses cached value if available, otherwise detects from the device
        or falls back to firmware_hint from config.

        Args:
            device_id: The device identifier.

        Returns:
            Major firmware version string ('3', '4', or '5').
        """
        if device_id in self._firmware_cache:
            return self._firmware_cache[device_id]

        device_cfg = self._config.devices.get(device_id)
        if device_cfg and device_cfg.firmware_hint:
            self._firmware_cache[device_id] = device_cfg.firmware_hint
            return device_cfg.firmware_hint

        # Try to detect from device
        try:
            client = self.get_client(device_id)
            response = client.send_command("SYSTEM PROPERTY")
            if response.is_ok and isinstance(response.data.get("Result"), dict):
                result = response.data["Result"]
                version_str = result.get("Version", "4")  # type: ignore[union-attr]
                if isinstance(version_str, str):
                    major = version_str.split(".")[0]
                    self._firmware_cache[device_id] = major
                    return major
        except Exception as exc:
            logger.warning("Could not detect firmware for '%s': %s", device_id, exc)

        # Default to 4.x
        self._firmware_cache[device_id] = "4"
        return "4"

    def set_firmware_version(self, device_id: str, version: str) -> None:
        """Manually set the cached firmware version for a device.

        Args:
            device_id: The device identifier.
            version: Major firmware version string.
        """
        self._firmware_cache[device_id] = version

    def close_all(self) -> None:
        """Disconnect all clients and clear the pool."""
        for device_id, client in self._clients.items():
            try:
                client.disconnect()
                logger.debug("Disconnected from '%s'", device_id)
            except Exception:
                pass
        self._clients.clear()
        self._firmware_cache.clear()
