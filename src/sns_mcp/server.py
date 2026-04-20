# SPDX-License-Identifier: Apache-2.0
"""MCP server entry point (STDIO transport)."""

from __future__ import annotations

import argparse
import logging

from fastmcp import FastMCP

from .capabilities.probe import probe_all_devices
from .capabilities.registry import CapabilityRegistry
from .client.device_manager import DeviceManager
from .config.loader import load_config
from .config.models import AppConfig
from .logging_config import setup_logging

logger = logging.getLogger("sns_mcp.server")


def _register_all_tools(
    mcp: FastMCP,
    config: AppConfig,
    manager: DeviceManager,
    registry: CapabilityRegistry,
) -> None:
    """Register all MCP tools on the FastMCP server instance.

    Tools requiring capabilities unavailable on ALL devices are skipped.

    Args:
        mcp: FastMCP server instance.
        config: Application configuration.
        manager: Device manager.
        registry: Capability registry.
    """
    from .tools import interfaces as iface_tools
    from .tools import objects as obj_tools
    from .tools import policy as pol_tools
    from .tools import system as sys_tools
    from .tools import users as user_tools
    from .tools import vpn as vpn_tools

    # ── Device list (always available) ──
    @mcp.tool()
    def sns_devices_list() -> str:
        """List all SNS devices configured in this MCP server.

        Returns device IDs, descriptions, tags, host addresses, and
        firmware hints. No credentials or passwords are ever returned.
        Use this tool first if you don't know which device_id to use.
        """
        return sys_tools.sns_devices_list(config, manager)

    # ── System tools (always) ──
    @mcp.tool()
    def sns_system_info_get(device_id: str) -> str:
        """Get general system information from the SNS device.

        Returns model name, firmware version, serial number, hostname,
        uptime, and build date.

        Args:
            device_id: ID of the target device as declared in config.yaml.
        """
        return sys_tools.sns_system_info_get(manager, device_id)

    @mcp.tool()
    def sns_system_licenses_list(device_id: str) -> str:
        """List all installed licenses and subscriptions with expiry dates.

        Args:
            device_id: ID of the target device as declared in config.yaml.
        """
        return sys_tools.sns_system_licenses_list(manager, device_id)

    @mcp.tool()
    def sns_system_stats_get(device_id: str) -> str:
        """Get live system resource statistics (CPU, memory, connections).

        This is a live monitoring call — not historical data.

        Args:
            device_id: ID of the target device as declared in config.yaml.
        """
        return sys_tools.sns_system_stats_get(manager, device_id)

    # ── HA (conditional) ──
    if registry.any_device_has("ha"):

        @mcp.tool()
        def sns_system_ha_status_get(device_id: str) -> str:
            """Get HA cluster status of the SNS device.

            Args:
                device_id: ID of the target device as declared in config.yaml.
            """
            return sys_tools.sns_system_ha_status_get(manager, device_id)

    # ── Filter rules ──
    if registry.any_device_has("filter"):

        @mcp.tool()
        def sns_filter_rules_list(
            device_id: str,
            slot: int | None = None,
            action_filter: str | None = None,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all filter (firewall) rules on the specified SNS device.

            Returns rules from the active policy slot by default.
            Use 'action_filter' to restrict by action (pass/block/log/decrypt).
            Use 'search' to filter by any text field.

            Does NOT return NAT rules — use sns_nat_rules_list.
            Does NOT modify any configuration.

            Args:
                device_id: ID of the target device.
                slot: Policy slot number (1-10). None = active slot.
                action_filter: Optional filter by rule action.
                search: Optional text search across all rule fields.
                page: Page number (1-indexed).
                page_size: Items per page (default 100).
            """
            return pol_tools.sns_filter_rules_list(
                manager,
                device_id,
                slot,
                action_filter,
                search,
                page,
                page_size,
            )

        @mcp.tool()
        def sns_policy_slots_list(device_id: str) -> str:
            """List all policy slots and identify the currently active slot.

            Args:
                device_id: ID of the target device.
            """
            return pol_tools.sns_policy_slots_list(manager, device_id)

    # ── NAT rules ──
    if registry.any_device_has("nat"):

        @mcp.tool()
        def sns_nat_rules_list(
            device_id: str,
            slot: int | None = None,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all NAT rules on the specified SNS device.

            Does NOT return filter rules — use sns_filter_rules_list.

            Args:
                device_id: ID of the target device.
                slot: Policy slot number (1-10).
                search: Optional text search.
                page: Page number.
                page_size: Items per page.
            """
            return pol_tools.sns_nat_rules_list(
                manager,
                device_id,
                slot,
                search,
                page,
                page_size,
            )

    # ── Objects ──
    if registry.any_device_has("objects"):

        @mcp.tool()
        def sns_network_objects_list(
            device_id: str,
            object_type: str = "all",
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all network objects on the SNS device.

            Args:
                device_id: ID of the target device.
                object_type: Filter by type (host/network/range/fqdn/all).
                search: Optional text search.
                page: Page number.
                page_size: Items per page.
            """
            return obj_tools.sns_network_objects_list(
                manager,
                device_id,
                object_type,
                search,
                page,
                page_size,
            )

        @mcp.tool()
        def sns_network_object_get(device_id: str, name: str) -> str:
            """Get full details of a single named network object.

            Args:
                device_id: ID of the target device.
                name: Exact name of the network object (case-sensitive).
            """
            return obj_tools.sns_network_object_get(manager, device_id, name)

        @mcp.tool()
        def sns_network_groups_list(
            device_id: str,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all network object groups and their members.

            Args:
                device_id: ID of the target device.
                search: Optional text search.
                page: Page number.
                page_size: Items per page.
            """
            return obj_tools.sns_network_groups_list(
                manager,
                device_id,
                search,
                page,
                page_size,
            )

        @mcp.tool()
        def sns_service_objects_list(
            device_id: str,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all service (port/protocol) objects.

            Args:
                device_id: ID of the target device.
                search: Optional text search.
                page: Page number.
                page_size: Items per page.
            """
            return obj_tools.sns_service_objects_list(
                manager,
                device_id,
                search,
                page,
                page_size,
            )

    # ── Interfaces ──
    if registry.any_device_has("interfaces"):

        @mcp.tool()
        def sns_interfaces_list(
            device_id: str,
            status_filter: str = "all",
        ) -> str:
            """List all network interfaces with their current status.

            Args:
                device_id: ID of the target device.
                status_filter: Filter by link state (up/down/all).
            """
            return iface_tools.sns_interfaces_list(
                manager,
                device_id,
                status_filter,
            )

    # ── Routing ──
    if registry.any_device_has("routing"):

        @mcp.tool()
        def sns_routing_table_get(
            device_id: str,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """Get the full routing table from the SNS device.

            Args:
                device_id: ID of the target device.
                search: Optional search on destination or gateway.
                page: Page number.
                page_size: Items per page.
            """
            return iface_tools.sns_routing_table_get(
                manager,
                device_id,
                search,
                page,
                page_size,
            )

    # ── VPN IPsec ──
    if registry.any_device_has("vpn_ipsec"):

        @mcp.tool()
        def sns_vpn_ipsec_config_list(
            device_id: str,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List all IPsec VPN tunnel configurations.

            Does NOT return live status — use sns_vpn_ipsec_status_list.

            Args:
                device_id: ID of the target device.
                search: Optional search on peer name or IP.
                page: Page number.
                page_size: Items per page.
            """
            return vpn_tools.sns_vpn_ipsec_config_list(
                manager,
                device_id,
                search,
                page,
                page_size,
            )

        @mcp.tool()
        def sns_vpn_ipsec_status_list(device_id: str) -> str:
            """List live status of all IPsec Security Associations.

            Args:
                device_id: ID of the target device.
            """
            return vpn_tools.sns_vpn_ipsec_status_list(manager, device_id)

    # ── VPN SSL ──
    if registry.any_device_has("vpn_ssl"):

        @mcp.tool()
        def sns_vpn_ssl_config_get(device_id: str) -> str:
            """Get SSL VPN configuration.

            Args:
                device_id: ID of the target device.
            """
            return vpn_tools.sns_vpn_ssl_config_get(manager, device_id)

        @mcp.tool()
        def sns_vpn_ssl_users_list(device_id: str) -> str:
            """List users currently connected via SSL VPN.

            Args:
                device_id: ID of the target device.
            """
            return vpn_tools.sns_vpn_ssl_users_list(manager, device_id)

    # ── Users ──
    if registry.any_device_has("users"):

        @mcp.tool()
        def sns_users_list(
            device_id: str,
            search: str | None = None,
            page: int = 1,
            page_size: int = 100,
        ) -> str:
            """List local user accounts on the SNS device.

            Never returns passwords or password hashes.

            Args:
                device_id: ID of the target device.
                search: Optional text search.
                page: Page number.
                page_size: Items per page.
            """
            return user_tools.sns_users_list(
                manager,
                device_id,
                search,
                page,
                page_size,
            )

        @mcp.tool()
        def sns_auth_config_get(device_id: str) -> str:
            """Get authentication method configuration.

            Never returns bind passwords or credentials.

            Args:
                device_id: ID of the target device.
            """
            return user_tools.sns_auth_config_get(manager, device_id)


def create_server(
    config_path: str | None = None,
    log_level: str | None = None,
) -> tuple[FastMCP, DeviceManager]:
    """Create and configure the MCP server.

    Args:
        config_path: Path to config YAML file.
        log_level: Override log level.

    Returns:
        Tuple of (FastMCP server, DeviceManager).
    """
    print("\n\033[96m[1/3] Loading configuration...\033[0m")
    config = load_config(config_path)

    if log_level:
        config.logging.level = log_level  # type: ignore[assignment]

    setup_logging(config.logging)

    # Warn if using the fallback demo config
    if getattr(config, "_is_demo_fallback", False):
        print(
            "\n\033[93m"
            "[!] NO CONFIGURATION FILE FOUND\n"
            "[!] Booting in DEMO mode connected to the public sandbox: sns-demo.stormshield.eu\n"
            "[!] To connect your own firewalls, run: sns-mcp --setup"
            "\033[0m\n"
        )
    else:
        print(f"\033[92m      Loaded {len(config.devices)} firewalls from configuration.\033[0m")

    # Warn about insecure HTTP binding
    if config.server.host == "0.0.0.0":
        logger.warning(
            "Server is binding to 0.0.0.0 — this exposes the MCP server "
            "to all network interfaces. Use a reverse proxy with TLS in production."
        )

    print("\033[96m[2/3] Connecting to firewalls and probing capabilities...\033[0m")
    manager = DeviceManager(config)
    registry = CapabilityRegistry()

    if config.capabilities.probe_on_start:
        try:
            caps = probe_all_devices(manager, config)
            registry.load(caps)
        except Exception as exc:
            logger.warning("Capability probing failed: %s", exc)
            # Load empty caps so all tools are registered
            registry.load(
                {
                    dev_id: dict.fromkeys(
                        [
                            "filter",
                            "nat",
                            "objects",
                            "routing",
                            "interfaces",
                            "vpn_ipsec",
                            "vpn_ssl",
                            "users",
                            "system",
                            "ha",
                            "monitor",
                        ],
                        True,
                    )
                    for dev_id in config.devices
                }
            )
    else:
        # Assume all capabilities available
        registry.load(
            {
                dev_id: dict.fromkeys(
                    [
                        "filter",
                        "nat",
                        "objects",
                        "routing",
                        "interfaces",
                        "vpn_ipsec",
                        "vpn_ssl",
                        "users",
                        "system",
                        "ha",
                        "monitor",
                    ],
                    True,
                )
                for dev_id in config.devices
            }
        )

    mcp = FastMCP(config.server.name)
    _register_all_tools(mcp, config, manager, registry)

    print("\033[96m[3/3] Server successfully initialized and ready!\033[0m")
    return mcp, manager


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Argument list (defaults to sys.argv).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="sns-mcp",
        description="Read-only MCP server for Stormshield SNS firewalls",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="Path to config.yaml file",
    )
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override log level",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the interactive configuration wizard",
    )
    parser.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Run the MCP server in the background (detached)",
    )
    return parser.parse_args(args)


def main_sync() -> None:
    """Synchronous entry point for the MCP server."""
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    args = parse_args()

    if args.setup:
        from .wizard import run_setup_wizard
        run_setup_wizard(args.config or "config/config.yaml")
        return

    if args.daemon:
        import sys
        import subprocess
        
        cmd = [sys.executable, "-m", "sns_mcp.server"]
        if args.config:
            cmd.extend(["--config", args.config])
        cmd.extend(["--transport", args.transport])
        if args.log_level:
            cmd.extend(["--log-level", args.log_level])
            
        print("\nStarting SNS MCP server in the background...")
        if sys.platform == "win32":
            subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen(cmd, start_new_session=True)
            
        print("Server successfully detached. You can close this terminal.\n")
        return

    if args.transport == "http":
        from .server_http import run_http

        run_http(args.config, args.log_level)
    else:
        mcp, manager = create_server(args.config, args.log_level)
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
            mcp.run(show_banner=False)
        finally:
            manager.close_all()


if __name__ == "__main__":
    main_sync()
