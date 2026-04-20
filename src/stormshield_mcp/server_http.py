# SPDX-License-Identifier: Apache-2.0
"""MCP server entry point (HTTP/SSE transport)."""

from __future__ import annotations

import logging

from .config.loader import load_config
from .server import create_server

logger = logging.getLogger("stormshield_mcp.server_http")


def run_http(
    config_path: str | None = None,
    log_level: str | None = None,
) -> None:
    """Start the MCP server in HTTP/SSE transport mode.

    Args:
        config_path: Path to config YAML file.
        log_level: Override log level.
    """
    config = load_config(config_path)
    mcp, manager = create_server(config_path, log_level)

    try:
        print(
            "\n+-----------------------------------------------------------------------------+\n"
            "|                                                                             |\n"
            "|   ███████╗███╗   ██╗███████╗    ███╗   ███╗ ██████╗██████╗                  |\n"
            "|   ██╔════╝████╗  ██║██╔════╝    ████╗ ████║██╔════╝██╔══██╗                 |\n"
            "|   ███████╗██╔██╗ ██║███████╗    ██╔████╔██║██║     ██████╔╝                 |\n"
            "|   ╚════██║██║╚██╗██║╚════██║    ██║╚██╔╝██║██║     ██╔═══╝                  |\n"
            "|   ███████║██║ ╚████║███████║    ██║ ╚═╝ ██║╚██████╗██║                      |\n"
            "|   ╚══════╝╚═╝  ╚═══╝╚══════╝    ╚═╝     ╚═╝ ╚═════╝╚═╝                      |\n"
            "|                                                                             |\n"
            "|                    Stormshield Network Security MCP Server                  |\n"
            "|                                                                             |\n"
            "+-----------------------------------------------------------------------------+\n",
            flush=True
        )
        mcp.run(
            transport="sse",
            host=config.server.host,
            port=config.server.port,
            show_banner=False,
        )
    finally:
        manager.close_all()


if __name__ == "__main__":
    run_http()
