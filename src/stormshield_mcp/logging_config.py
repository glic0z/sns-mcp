# SPDX-License-Identifier: Apache-2.0
"""Structured logging configuration with credential scrubbing."""

from __future__ import annotations

import json
import logging
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config.models import LoggingConfig

_SENSITIVE_PATTERNS = re.compile(r"(password|passwd|secret|token)", re.IGNORECASE)
_REDACTION_TEXT = "***REDACTED***"


class SensitiveFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records.

    Any log record whose message or arguments contain the strings
    'password', 'passwd', 'secret', or 'token' will have those values
    replaced with '***REDACTED***'.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive fields in log messages."""
        if record.msg and isinstance(record.msg, str):
            record.msg = _SENSITIVE_PATTERNS.sub(_REDACTION_TEXT, record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: _REDACTION_TEXT
                    if isinstance(v, str) and _SENSITIVE_PATTERNS.search(v)
                    else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    _REDACTION_TEXT if isinstance(a, str) and _SENSITIVE_PATTERNS.search(a) else a
                    for a in record.args
                )
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(config: LoggingConfig | None = None) -> None:
    """Configure logging based on application config.

    Args:
        config: Logging configuration. If None, uses sensible defaults.
    """
    level_str = "INFO"
    fmt = "json"
    log_file: str | None = None

    if config is not None:
        level_str = config.level
        fmt = config.format
        log_file = config.file

    root_logger = logging.getLogger("stormshield_mcp")
    root_logger.setLevel(getattr(logging, level_str, logging.INFO))

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Add sensitive filter
    sensitive_filter = SensitiveFilter()
    root_logger.addFilter(sensitive_filter)

    if fmt == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
