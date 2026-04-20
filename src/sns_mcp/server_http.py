# SPDX-License-Identifier: Apache-2.0
"""MCP server entry point (HTTP/SSE transport)."""

from __future__ import annotations

import logging

from .config.loader import load_config
from .server import create_server

logger = logging.getLogger("sns_mcp.server_http")


def run_http(
    config_path: str | None = None,
    log_level: str | None = None,
) -> None:
    """Start the MCP server in HTTP/SSE transport mode.

    Args:
        config_path: Path to config YAML file.
        log_level: Override log level.
    """
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    config = load_config(config_path)
    mcp, manager = create_server(config_path, log_level)

    try:
        CYAN = "\033[96m"
        BLUE = "\033[94m"
        MAGENTA = "\033[95m"
        RED = "\033[91m"
        RESET = "\033[0m"
        print(
            f"\n{CYAN}+-----------------------------------------------------------------------------+{RESET}\n"
            f"{CYAN}|{RESET}                                                                             {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}███████╗███╗   ██╗███████╗    ███╗   ███╗ ██████╗██████╗{RESET}                  {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}██╔════╝████╗  ██║██╔════╝    ████╗ ████║██╔════╝██╔══██╗{RESET}                 {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}███████╗██╔██╗ ██║███████╗    ██╔████╔██║██║     ██████╔╝{RESET}                 {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}╚════██║██║╚██╗██║╚════██║    ██║╚██╔╝██║██║     ██╔═══╝ {RESET}                 {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}███████║██║ ╚████║███████║    ██║ ╚═╝ ██║╚██████╗██║     {RESET}                 {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}   {BLUE}╚══════╝╚═╝  ╚═══╝╚══════╝    ╚═╝     ╚═╝ ╚═════╝╚═╝     {RESET}                 {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}                                                                             {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}                    {MAGENTA}Stormshield Network Security MCP Server{RESET}                  {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}                                                                             {CYAN}|{RESET}\n"
            f"{CYAN}|{RESET}                   Built by glicoz and claude with love {RED}❤{RESET}                    {CYAN}|{RESET}\n"
            f"{CYAN}+-----------------------------------------------------------------------------+{RESET}\n",
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
