# SPDX-License-Identifier: Apache-2.0
"""Unit tests for all parsers using fixture data."""

from __future__ import annotations

from conftest import load_fixture
from sns_mcp.parsers.filter_rules import FilterRuleParser
from sns_mcp.parsers.interfaces import InterfaceParser
from sns_mcp.parsers.nat_rules import NatRuleParser
from sns_mcp.parsers.objects import ObjectParser, ServiceParser
from sns_mcp.parsers.routing import RoutingParser
from sns_mcp.parsers.system import (
    AuthConfigParser,
    MonitorStatParser,
    SystemHAParser,
    SystemLicenseParser,
    SystemPropertyParser,
)
from sns_mcp.parsers.vpn import (
    VpnIpsecConfigParser,
    VpnIpsecSAParser,
)

# ═══════════════════════════════════════════════════════
# Filter Rule Parser Tests
# ═══════════════════════════════════════════════════════


class TestFilterRuleParser:
    """Tests for FilterRuleParser."""

    def test_parse_sns4_rules(self) -> None:
        """Parse SNS 4.x filter rules fixture."""
        response = load_fixture("filter_show_sns4.txt")
        rules = FilterRuleParser.parse(response.data, "4")
        assert len(rules) == 10
        assert rules[0]["name"] == "rule_allow_http"
        assert rules[0]["action"] == "pass"
        assert rules[0]["enabled"] is True
        assert rules[0]["rank"] == 1
        assert "Network_LAN" in rules[0]["source"]["hosts"]
        assert "http" in rules[0]["service"]

    def test_parse_sns5_rules(self) -> None:
        """Parse SNS 5.x filter rules with rulename field."""
        response = load_fixture("filter_show_sns5.txt")
        rules = FilterRuleParser.parse(response.data, "5")
        assert len(rules) == 10
        assert rules[0]["name"] == "rule_allow_http"
        assert rules[9]["name"] == "rule_default_deny"
        assert rules[9]["action"] == "block"

    def test_parse_empty_rules(self) -> None:
        """Parse empty filter rules fixture."""
        response = load_fixture("filter_show_empty.txt")
        rules = FilterRuleParser.parse(response.data, "4")
        assert len(rules) == 0

    def test_block_rules_present(self) -> None:
        """Verify block rules are correctly parsed."""
        response = load_fixture("filter_show_sns4.txt")
        rules = FilterRuleParser.parse(response.data, "4")
        block_rules = [r for r in rules if r["action"] == "block"]
        assert len(block_rules) >= 2

    def test_rule_comments_preserved(self) -> None:
        """Ensure comments are preserved in parsed rules."""
        response = load_fixture("filter_show_sns4.txt")
        rules = FilterRuleParser.parse(response.data, "4")
        assert rules[0]["comment"] == "Allow HTTP to web server"

    def test_parse_single_rule(self) -> None:
        """Parse data containing a single rule dict."""
        data = {"Result": {"name": "single_rule", "action": "pass", "rank": "1", "status": "on"}}
        rules = FilterRuleParser.parse(data, "4")
        assert len(rules) == 1
        assert rules[0]["name"] == "single_rule"

    def test_parse_malformed_data(self) -> None:
        """Parse data with missing fields gracefully."""
        data = {"Result": [{"action": "pass"}]}
        rules = FilterRuleParser.parse(data, "4")
        assert len(rules) == 1
        assert rules[0]["name"] == ""
        assert rules[0]["action"] == "pass"


# ═══════════════════════════════════════════════════════
# NAT Rule Parser Tests
# ═══════════════════════════════════════════════════════


class TestNatRuleParser:
    """Tests for NatRuleParser."""

    def test_parse_nat_rules(self) -> None:
        """Parse NAT rules fixture."""
        response = load_fixture("nat_show_sns4.txt")
        rules = NatRuleParser.parse(response.data, "4")
        assert len(rules) == 5
        assert rules[0]["name"] == "nat_web_http"
        assert rules[0]["original_port"] == "80"
        assert rules[0]["translated_destination"] == "srv_web"

    def test_disabled_nat_rule(self) -> None:
        """Verify disabled NAT rules are flagged."""
        response = load_fixture("nat_show_sns4.txt")
        rules = NatRuleParser.parse(response.data, "4")
        disabled = [r for r in rules if not r["enabled"]]
        assert len(disabled) == 1
        assert disabled[0]["name"] == "nat_vpn_pool"

    def test_parse_empty_nat(self) -> None:
        """Parse empty result set."""
        data: dict[str, list[dict[str, str]]] = {"Result": []}
        rules = NatRuleParser.parse(data, "4")
        assert len(rules) == 0


# ═══════════════════════════════════════════════════════
# Object Parser Tests
# ═══════════════════════════════════════════════════════


class TestObjectParser:
    """Tests for ObjectParser."""

    def test_parse_host_objects(self) -> None:
        """Parse host objects fixture."""
        response = load_fixture("object_show_hosts.txt")
        objects = ObjectParser.parse(response.data, "4")
        assert len(objects) == 8
        assert objects[0]["name"] == "srv_web"
        assert objects[0]["ip"] == "192.168.1.10"
        assert objects[0]["type"] == "host"

    def test_parse_network_objects(self) -> None:
        """Parse network objects fixture."""
        response = load_fixture("object_show_networks.txt")
        objects = ObjectParser.parse(response.data, "4")
        assert len(objects) == 4
        assert objects[0]["name"] == "Network_LAN"
        assert objects[0]["ip"] == "192.168.1.0"

    def test_builtin_flag(self) -> None:
        """Verify builtin flag is parsed."""
        response = load_fixture("object_show_hosts.txt")
        objects = ObjectParser.parse(response.data, "4")
        builtin = [o for o in objects if o["builtin"]]
        assert len(builtin) >= 1


class TestServiceParser:
    """Tests for ServiceParser."""

    def test_parse_services(self) -> None:
        """Parse service objects fixture."""
        response = load_fixture("service_show.txt")
        services = ServiceParser.parse(response.data, "4")
        assert len(services) == 6
        assert services[0]["name"] == "http"
        assert services[0]["port"] == "80"
        assert services[0]["protocol"] == "tcp"

    def test_all_builtin(self) -> None:
        """Verify all fixture services are builtin."""
        response = load_fixture("service_show.txt")
        services = ServiceParser.parse(response.data, "4")
        assert all(s["builtin"] for s in services)


# ═══════════════════════════════════════════════════════
# Interface Parser Tests
# ═══════════════════════════════════════════════════════


class TestInterfaceParser:
    """Tests for InterfaceParser."""

    def test_parse_interfaces(self) -> None:
        """Parse interface fixture."""
        response = load_fixture("interface_show.txt")
        ifaces = InterfaceParser.parse(response.data, "4")
        assert len(ifaces) == 4

    def test_interface_status(self) -> None:
        """Verify up/down status parsing."""
        response = load_fixture("interface_show.txt")
        ifaces = InterfaceParser.parse(response.data, "4")
        up = [i for i in ifaces if i["status"] == "up"]
        down = [i for i in ifaces if i["status"] == "down"]
        assert len(up) == 3
        assert len(down) == 1

    def test_vlan_interface(self) -> None:
        """Verify VLAN interface parsing."""
        response = load_fixture("interface_show.txt")
        ifaces = InterfaceParser.parse(response.data, "4")
        vlans = [i for i in ifaces if i["type"] == "vlan"]
        assert len(vlans) == 1
        assert vlans[0]["vlan_id"] == "10"


# ═══════════════════════════════════════════════════════
# Routing Parser Tests
# ═══════════════════════════════════════════════════════


class TestRoutingParser:
    """Tests for RoutingParser."""

    def test_parse_routes(self) -> None:
        """Parse route fixture."""
        response = load_fixture("route_show.txt")
        routes = RoutingParser.parse(response.data, "4")
        assert len(routes) == 4

    def test_default_route(self) -> None:
        """Verify default route is present."""
        response = load_fixture("route_show.txt")
        routes = RoutingParser.parse(response.data, "4")
        default = [r for r in routes if r["destination"] == "0.0.0.0"]
        assert len(default) == 1
        assert default[0]["gateway"] == "203.0.113.1"

    def test_connected_routes(self) -> None:
        """Verify connected routes."""
        response = load_fixture("route_show.txt")
        routes = RoutingParser.parse(response.data, "4")
        connected = [r for r in routes if r["type"] == "connected"]
        assert len(connected) == 2


# ═══════════════════════════════════════════════════════
# VPN Parser Tests
# ═══════════════════════════════════════════════════════


class TestVpnIpsecConfigParser:
    """Tests for VpnIpsecConfigParser."""

    def test_parse_ipsec_config(self) -> None:
        """Parse IPsec config fixture."""
        response = load_fixture("vpn_ipsec_config.txt")
        tunnels = VpnIpsecConfigParser.parse(response.data, "4")
        assert len(tunnels) == 2
        assert tunnels[0]["name"] == "peer_paris_lyon"
        assert tunnels[0]["remote_gateway"] == "198.51.100.1"

    def test_ipsec_auth_methods(self) -> None:
        """Verify different auth methods."""
        response = load_fixture("vpn_ipsec_config.txt")
        tunnels = VpnIpsecConfigParser.parse(response.data, "4")
        assert tunnels[0]["auth_method"] == "psk"
        assert tunnels[1]["auth_method"] == "certificate"


class TestVpnIpsecSAParser:
    """Tests for VpnIpsecSAParser."""

    def test_parse_ipsec_sa(self) -> None:
        """Parse IPsec SA fixture."""
        response = load_fixture("vpn_ipsec_sa.txt")
        sas = VpnIpsecSAParser.parse(response.data, "4")
        assert len(sas) == 2

    def test_sa_states(self) -> None:
        """Verify SA state parsing."""
        response = load_fixture("vpn_ipsec_sa.txt")
        sas = VpnIpsecSAParser.parse(response.data, "4")
        assert sas[0]["state"] == "established"
        assert sas[1]["state"] == "down"

    def test_sa_byte_counters(self) -> None:
        """Verify byte counters."""
        response = load_fixture("vpn_ipsec_sa.txt")
        sas = VpnIpsecSAParser.parse(response.data, "4")
        assert sas[0]["bytes_in"] == "1048576"
        assert sas[1]["bytes_in"] == "0"


# ═══════════════════════════════════════════════════════
# System Parser Tests
# ═══════════════════════════════════════════════════════


class TestSystemPropertyParser:
    """Tests for SystemPropertyParser."""

    def test_parse_system_property(self) -> None:
        """Parse system property fixture."""
        response = load_fixture("system_property.txt")
        info = SystemPropertyParser.parse(response.data, "4")
        assert info["model"] == "SN710"
        assert info["version"] == "4.3.22"
        assert info["serial"] == "U70XXSN71012345"
        assert info["hostname"] == "paris-fw-01"


class TestSystemLicenseParser:
    """Tests for SystemLicenseParser."""

    def test_parse_licenses(self) -> None:
        """Parse licenses fixture."""
        response = load_fixture("system_licenses.txt")
        licenses = SystemLicenseParser.parse(response.data, "4")
        assert len(licenses) == 5

    def test_license_statuses(self) -> None:
        """Verify different license statuses."""
        response = load_fixture("system_licenses.txt")
        licenses = SystemLicenseParser.parse(response.data, "4")
        active = [lic for lic in licenses if lic["status"] == "active"]
        expired = [lic for lic in licenses if lic["status"] == "expired"]
        missing = [lic for lic in licenses if lic["status"] == "missing"]
        assert len(active) >= 2
        assert len(expired) == 1
        assert len(missing) == 1


class TestSystemHAParser:
    """Tests for SystemHAParser."""

    def test_parse_ha_active(self) -> None:
        """Parse HA active node fixture."""
        response = load_fixture("system_ha_active.txt")
        ha = SystemHAParser.parse(response.data, "4")
        assert ha["enabled"] is True
        assert ha["mode"] == "active-passive"
        assert ha["role"] == "active"
        assert ha["sync_state"] == "synchronized"


class TestMonitorStatParser:
    """Tests for MonitorStatParser."""

    def test_parse_monitor_stat(self) -> None:
        """Parse monitoring stats fixture."""
        response = load_fixture("monitor_stat.txt")
        stats = MonitorStatParser.parse(response.data, "4")
        assert stats["cpu_percent"] == "12"
        assert stats["memory_percent"] == "45"
        assert stats["connections"] == "3241"


class TestAuthConfigParser:
    """Tests for AuthConfigParser credential stripping."""

    def test_strips_passwords(self) -> None:
        """Ensure passwords are never in parsed output."""
        data = {
            "Result": {
                "method": "ldap",
                "server": "10.0.0.100",
                "password": "s3cret",
                "bindpw": "anothersecret",
                "basedn": "dc=example,dc=com",
            }
        }
        result = AuthConfigParser.parse(data, "4")
        assert "password" not in result
        assert "bindpw" not in result
        assert result["method"] == "ldap"
        assert result["server"] == "10.0.0.100"
