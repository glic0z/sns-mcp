# SPDX-License-Identifier: Apache-2.0
"""Thin async wrapper around the Stormshield SSLClient."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger("stormshield_mcp.client")


@dataclass
class SNSResponse:
    """Parsed response from an SNS CLI command.

    Attributes:
        ret: Return code from the appliance (e.g. '00a00100' for OK).
        code: Numeric return code.
        msg: Human-readable message from the appliance.
        format: Response format ('section' or 'section_line').
        data: Parsed response data as a dictionary.
        raw: Raw text output for debugging.
    """

    ret: str = ""
    code: str = ""
    msg: str = ""
    format: str = ""
    data: dict[str, list[dict[str, str]] | dict[str, str] | str] = field(default_factory=dict)
    raw: str = ""

    @property
    def is_ok(self) -> bool:
        """Check if the response indicates success."""
        return self.ret in {"00a00100", "00a01000"}

    @property
    def is_not_licensed(self) -> bool:
        """Check if the feature is not licensed."""
        return self.ret == "00b00013"

    @property
    def is_not_found(self) -> bool:
        """Check if the command/object was not found."""
        return self.ret in {"00b00001", "00b00014"}


class SNSClientProtocol(Protocol):
    """Protocol for SNS client implementations."""

    def connect(self) -> bool:
        """Connect to the SNS device."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the SNS device."""
        ...

    def send_command(self, command: str) -> SNSResponse:
        """Send a CLI command and return the parsed response."""
        ...


class SNSClient:
    """Thin wrapper around the Stormshield SNS SSL client.

    Wraps the official stormshield.sns.sslclient.SSLClient to provide
    a consistent interface and async support via loop.run_in_executor.
    """

    def __init__(
        self,
        host: str,
        port: int = 443,
        user: str = "",
        password: str = "",
        sslverifyhost: bool = False,
        sslverifypeer: bool = False,
        cabundle: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize SNS client configuration.

        Args:
            host: SNS appliance hostname or IP address.
            port: HTTPS port (default 443).
            user: Authentication username.
            password: Authentication password.
            sslverifyhost: Whether to verify the SSL hostname.
            sslverifypeer: Whether to verify the SSL peer certificate.
            cabundle: Path to CA bundle PEM file.
            timeout: Command timeout in seconds.
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._sslverifyhost = sslverifyhost
        self._sslverifypeer = sslverifypeer
        self._cabundle = cabundle
        self._timeout = timeout
        self._real_client: Any = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to the SNS device using the official SSL client.

        Returns:
            True if connection was successful.
        """
        try:
            from stormshield.sns.sslclient import SSLClient

            self._real_client = SSLClient(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                sslverifyhost=self._sslverifyhost,
                sslverifypeer=self._sslverifypeer,
                cabundle=self._cabundle or "",
                timeout=self._timeout,
            )
            self._connected = True
            logger.info("Connected to SNS device at %s:%d", self._host, self._port)
            return True
        except ImportError:
            logger.warning("stormshield.sns.sslclient not available — running in mock/test mode")
            self._connected = False
            return False
        except Exception as exc:
            logger.error("Failed to connect to %s:%d — %s", self._host, self._port, exc)
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the SNS device."""
        if self._real_client is not None:
            import contextlib

            with contextlib.suppress(Exception):
                self._real_client.disconnect()
            self._real_client = None
        self._connected = False

    def send_command(self, command: str) -> SNSResponse:
        """Send a CLI command to the SNS device.

        Args:
            command: SNS CLI command string.

        Returns:
            Parsed SNSResponse.

        Raises:
            ConnectionError: If not connected to the device.
        """
        if self._real_client is None:
            raise ConnectionError(f"Not connected to SNS device at {self._host}")

        try:
            response = self._real_client.send_command(command)
            return SNSResponse(
                ret=getattr(response, "ret", ""),
                code=getattr(response, "code", ""),
                msg=getattr(response, "msg", ""),
                format=getattr(response, "format", ""),
                data=getattr(response, "data", {}) or {},
                raw=getattr(response, "output", ""),
            )
        except Exception as exc:
            logger.error("Command '%s' failed on %s: %s", command, self._host, exc)
            raise

    async def async_send_command(self, command: str) -> SNSResponse:
        """Async wrapper for send_command using run_in_executor.

        Args:
            command: SNS CLI command string.

        Returns:
            Parsed SNSResponse.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_command, command)
