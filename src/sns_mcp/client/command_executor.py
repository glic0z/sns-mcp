# SPDX-License-Identifier: Apache-2.0
"""Command dispatch with read-only enforcement, firmware awareness, and retry logic."""

from __future__ import annotations

import logging
import re

from .sns_client import SNSClient, SNSResponse

logger = logging.getLogger("sns_mcp.client.command_executor")

# Commands that would modify device configuration — BLOCKED
WRITE_COMMAND_PREFIXES = (
    "CONFIG",
    "OBJECT ADD",
    "OBJECT DEL",
    "OBJECT MODIFY",
    "FILTER ADD",
    "FILTER DEL",
    "FILTER MODIFY",
    "FILTER ACTIVATE",
    "NAT ADD",
    "NAT DEL",
    "NAT MODIFY",
    "ROUTE ADD",
    "ROUTE DEL",
    "ROUTE MODIFY",
    "USER ADD",
    "USER DEL",
    "USER MODIFY",
    "SERVICE ADD",
    "SERVICE DEL",
    "SERVICE MODIFY",
    "INTERFACE MODIFY",
    "SYSTEM UPDATE",
    "SYSTEM REBOOT",
    "SYSTEM SHUTDOWN",
    "HA FAILOVER",
    "MODIFY",
    "DELETE",
    "ACTIVATE",
)

# Allowed characters for sanitized input
ALLOWED_CHARS = re.compile(r"^[a-zA-Z0-9_\-\.:\/ ]+$")

# Firmware-aware command mappings
FIRMWARE_COMMANDS: dict[str, dict[str, str | None]] = {
    "ztna_show": {
        "3": None,
        "4": None,
        "5": "ZTNA SHOW",
    },
    "global_filter_show": {
        "3": None,
        "4": "FILTER GLOBAL SHOW",
        "5": "FILTER GLOBAL SHOW",
    },
    "sdwan_show": {
        "3": None,
        "4": None,
        "5": "SDWAN SHOW",
    },
}


class ReadOnlyViolationError(RuntimeError):
    """Raised when a write command is attempted."""


class CapabilityUnavailableError(Exception):
    """Raised when a feature is not available on the device."""

    def __init__(self, capability: str, device_id: str, reason: str = "") -> None:
        self.capability = capability
        self.device_id = device_id
        self.reason = reason
        super().__init__(reason or f"Feature '{capability}' not available on device '{device_id}'")


class CommandError(Exception):
    """Raised when the SNS appliance returns an error code."""

    def __init__(self, code: str, message: str, command: str) -> None:
        self.code = code
        self.sns_message = message
        self.command = command
        super().__init__(f"SNS error {code}: {message} (command: {command})")


class ParseError(Exception):
    """Raised when response parsing fails."""


def assert_read_only(command: str) -> None:
    """Verify a command is read-only before sending it to the device.

    Args:
        command: The CLI command string to validate.

    Raises:
        ReadOnlyViolationError: If the command would modify device state.
    """
    upper = command.strip().upper()
    for prefix in WRITE_COMMAND_PREFIXES:
        if upper.startswith(prefix):
            raise ReadOnlyViolationError(
                f"SAFETY VIOLATION: Write command blocked: {command!r}. "
                "sns-mcp is a read-only tool."
            )


def sanitize_input(value: str, field_name: str) -> str:
    """Sanitize user input to prevent command injection in CLI parameters.

    Args:
        value: The input string to sanitize.
        field_name: Name of the field being sanitized (for error messages).

    Returns:
        The trimmed, validated string.

    Raises:
        ValueError: If the input contains disallowed characters.
    """
    stripped = value.strip()
    if not stripped:
        return stripped
    if not ALLOWED_CHARS.match(stripped):
        raise ValueError(
            f"Parameter '{field_name}' contains invalid characters. "
            "Only alphanumeric, dash, dot, colon, slash, and space are allowed."
        )
    return stripped


def execute_command(
    client: SNSClient,
    command: str,
    device_id: str = "",
) -> SNSResponse:
    """Execute a read-only command on the SNS device.

    Enforces the read-only constraint and handles common error codes.

    Args:
        client: Connected SNS client instance.
        command: CLI command string to execute.
        device_id: Device identifier for error messages.

    Returns:
        Parsed SNSResponse.

    Raises:
        ReadOnlyViolationError: If command would write to the device.
        CapabilityUnavailableError: If the feature is not licensed.
        CommandError: If the device returns an error response.
    """
    assert_read_only(command)

    logger.debug("[%s] Executing: %s", device_id, command)
    response = client.send_command(command)

    if response.is_ok:
        return response

    if response.is_not_licensed:
        raise CapabilityUnavailableError(
            capability=command.split()[0].lower(),
            device_id=device_id,
            reason=f"Feature not licensed or unavailable: {response.msg}",
        )

    if response.ret == "00b00030":
        from .device_manager import AuthenticationError

        raise AuthenticationError(device_id)

    if response.is_not_found:
        raise CommandError(
            code=response.ret,
            message=response.msg or "Command or object not found",
            command=command,
        )

    raise CommandError(
        code=response.ret,
        message=response.msg or "Unknown error",
        command=command,
    )


def execute_firmware_aware(
    client: SNSClient,
    command_key: str,
    firmware: str,
    device_id: str = "",
    fallback: str | None = None,
) -> SNSResponse:
    """Execute a firmware-version-aware command.

    Looks up the correct command syntax for the given firmware version
    and falls back to an alternative if needed.

    Args:
        client: Connected SNS client instance.
        command_key: Logical command key in FIRMWARE_COMMANDS.
        firmware: Major firmware version ('3', '4', or '5').
        device_id: Device identifier for error messages.
        fallback: Fallback command if no firmware-specific one exists.

    Returns:
        Parsed SNSResponse.

    Raises:
        CapabilityUnavailableError: If the command is not available on this firmware.
    """
    command = FIRMWARE_COMMANDS.get(command_key, {}).get(firmware, fallback)
    if command is None:
        raise CapabilityUnavailableError(
            capability=command_key,
            device_id=device_id,
            reason=f"Command '{command_key}' is not available on SNS firmware {firmware}.x",
        )
    return execute_command(client, command, device_id)
