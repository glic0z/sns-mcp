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
            "server": {"name": "sns-mcp", "host": "127.0.0.1", "port": 8000},
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
        
        print(f"\n{CYAN}Authentication Method:{RESET}")
        print("  [1] Password (Traditional)")
        print("  [2] Browser Cookie (More Secure, no password stored)")
        auth_choice = input(f"Select [1]: ").strip() or "1"

        auth_method = "cookie" if auth_choice == "2" else "password"
        password = None
        cookie = None

        if auth_method == "password":
            password = input(f"{CYAN}Password{RESET}: ").strip()
            env_var_name = f"SNS_PASSWORD_{dev_id.upper()}"
            secret_val = password
        else:
            import webbrowser
            print(f"\n{YELLOW}Opening browser to https://{host}:{port}/admin/admin.html{RESET}")
            print("1. Log in to your firewall.")
            print("2. Press F12 to open Developer Tools.")
            print("3. Go to the Application/Storage tab -> Cookies.")
            print("4. Copy the value of the 'SNS_webadmin' cookie.")
            try:
                webbrowser.open(f"https://{host}:{port}/admin/admin.html")
            except Exception:
                pass
            cookie = input(f"{CYAN}Paste Cookie Value{RESET}: ").strip()
            env_var_name = f"SNS_COOKIE_{dev_id.upper()}"
            secret_val = cookie
        
        print(f"\n{YELLOW}Testing connection to {host}:{port}...{RESET}")
        
        try:
            from stormshield.sns.sslclient import SSLClient
            from .client.sns_client import CookieSSLClient
            
            if auth_method == "cookie":
                client = CookieSSLClient._create_patched_client(
                    host=host,
                    port=port,
                    cookie=cookie,
                    sslverifypeer=False,
                    sslverifyhost=False,
                    timeout=10,
                )
            else:
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
        except ValueError as e:
            if str(e) == "AUTH_EXPIRED":
                print(f"{RED}✗ Connection failed: Cookie is expired or invalid!{RESET}")
            else:
                print(f"{RED}✗ Error: {e}{RESET}")
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
        env_lines.append(f'{env_var_name}="{secret_val}"\n')
        
        with open(env_file, "w") as f:
            f.writelines(env_lines)
            
        print(f"{GREEN}✓ Saved secret to .env as {env_var_name}{RESET}")

        # Update config
        device_entry = {
            "host": host,
            "port": port,
            "user": user,
            "ssl_verify_host": False,
            "ssl_verify_peer": False,
            "timeout": 30
        }
        if auth_method == "cookie":
            device_entry["cookie"] = f"${{{env_var_name}}}"
        else:
            device_entry["password"] = f"${{{env_var_name}}}"
            
        config["devices"][dev_id] = device_entry
        
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            yaml.dump(config, f, sort_keys=False, default_flow_style=False)
            
        print(f"{GREEN}✓ Saved configuration to {config_file}{RESET}")

        add_another = input(f"\nAdd another firewall? (y/N): ").strip().lower()
        if add_another != 'y':
            break

    print(f"\n{CYAN}=== Wizard Complete ==={RESET}")
    print(f"You can now run the MCP server with: {GREEN}sns-mcp --config {config_path}{RESET}")
    sys.exit(0)
