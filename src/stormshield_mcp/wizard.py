import os
import sys
import yaml
import json
from pathlib import Path

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def run_setup_wizard(config_path: str = "config/config.yaml"):
    """Run an interactive CLI wizard to configure SNS devices."""
    print(f"\n{CYAN}=== Stormshield MCP Setup Wizard ==={RESET}")
    print("This wizard will help you configure your SNS devices and securely store credentials.")
    
    config_file = Path(config_path)
    env_file = Path(".env")
    
    # Load existing config or create skeleton
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {
            "logging": {"level": "INFO", "redact_secrets": True},
            "server": {"name": "stormshield-mcp", "host": "127.0.0.1", "port": 8000},
            "devices": {}
        }
        
    if "devices" not in config or not config["devices"]:
        config["devices"] = {}

    while True:
        print(f"\n{YELLOW}--- Add a New Firewall ---{RESET}")
        
        dev_id = input(f"{CYAN}Device ID{RESET} (e.g., 'primary_fw'): ").strip()
        if not dev_id:
            print(f"{RED}Device ID cannot be empty.{RESET}")
            continue
            
        host = input(f"{CYAN}Hostname/IP{RESET} (e.g., '192.168.1.254'): ").strip()
        port_str = input(f"{CYAN}Port{RESET} [443]: ").strip()
        port = int(port_str) if port_str.isdigit() else 443
        
        user = input(f"{CYAN}Username{RESET} [admin]: ").strip() or "admin"
        password = input(f"{CYAN}Password{RESET}: ").strip()
        
        env_var_name = f"SNS_PASSWORD_{dev_id.upper()}"
        
        print(f"\n{YELLOW}Testing connection to {host}:{port}...{RESET}")
        
        try:
            from stormshield.sns.sslclient import SSLClient
            client = SSLClient(
                host=host,
                port=port,
                user=user,
                password=password,
                sslverifypeer=False,
                sslverifyhost=False,
                timeout=10,
                autoconnect=False
            )
            if client.connect():
                print(f"{GREEN}✓ Connection successful!{RESET}")
                try:
                    client.disconnect()
                except Exception:
                    pass
            else:
                print(f"{RED}✗ Connection failed!{RESET}")
                retry = input(f"Do you want to add this device anyway? (y/N): ").strip().lower()
                if retry != 'y':
                    continue
        except Exception as e:
            print(f"{RED}✗ Error during connection test: {e}{RESET}")
            retry = input(f"Do you want to add this device anyway? (y/N): ").strip().lower()
            if retry != 'y':
                continue

        # Save to .env
        env_lines = []
        if env_file.exists():
            with open(env_file, "r") as f:
                env_lines = f.readlines()
        
        # Remove old env var if exists, then append
        env_lines = [line for line in env_lines if not line.startswith(f"{env_var_name}=")]
        env_lines.append(f'{env_var_name}="{password}"\n')
        
        with open(env_file, "w") as f:
            f.writelines(env_lines)
            
        print(f"{GREEN}✓ Saved password to .env as {env_var_name}{RESET}")

        # Update config
        config["devices"][dev_id] = {
            "host": host,
            "port": port,
            "user": user,
            "password": f"${{{env_var_name}}}",
            "ssl_verify_host": False,
            "ssl_verify_peer": False,
            "timeout": 30
        }
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
            
        print(f"{GREEN}✓ Saved configuration to {config_file}{RESET}")

        add_another = input(f"\nAdd another firewall? (y/N): ").strip().lower()
        if add_another != 'y':
            break

    print(f"\n{CYAN}=== Wizard Complete ==={RESET}")
    print(f"You can now run the MCP server with: {GREEN}stormshield-mcp --config {config_path}{RESET}")
    sys.exit(0)
