#!/usr/bin/env python3
"""
Toggle development mode (database-only search) on/off in .env file.
Usage:
    python toggle_dev_mode.py on   # Enable dev mode (database only)
    python toggle_dev_mode.py off  # Disable dev mode (use Google API)
    python toggle_dev_mode.py      # Show current status
"""

import os
import sys

ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
DEV_MODE_KEY = 'USE_DB_ONLY_MODE'


def read_env():
    """Read .env file and return as dict"""
    if not os.path.exists(ENV_FILE):
        print(f"❌ Error: .env file not found at {ENV_FILE}")
        sys.exit(1)
    
    env_vars = {}
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def write_env(env_vars):
    """Write env dict back to .env file, preserving comments"""
    with open(ENV_FILE, 'r') as f:
        lines = f.readlines()
    
    with open(ENV_FILE, 'w') as f:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in env_vars:
                    f.write(f"{key}={env_vars[key]}\n")
                else:
                    f.write(line)
            else:
                f.write(line)


def get_current_status():
    """Get current dev mode status"""
    env_vars = read_env()
    value = env_vars.get(DEV_MODE_KEY, 'False')
    return value.lower() in ['true', '1', 'yes', 'on']


def add_dev_mode_if_missing():
    """Add USE_DB_ONLY_MODE to .env if it doesn't exist"""
    with open(ENV_FILE, 'r') as f:
        content = f.read()
    
    if DEV_MODE_KEY not in content:
        print(f"📝 Adding {DEV_MODE_KEY} to .env file...")
        with open(ENV_FILE, 'a') as f:
            f.write(f"\n# Development Mode - Set to True to use database-only search\n")
            f.write(f"{DEV_MODE_KEY}=False\n")


def set_dev_mode(enabled):
    """Set dev mode on or off"""
    add_dev_mode_if_missing()
    env_vars = read_env()
    env_vars[DEV_MODE_KEY] = 'True' if enabled else 'False'
    write_env(env_vars)
    
    status = "ENABLED" if enabled else "DISABLED"
    emoji = "🔧" if enabled else "🚀"
    mode = "Database-only (no API calls)" if enabled else "Google Places API"
    
    print(f"\n{emoji} Development Mode {status}")
    print(f"   Mode: {mode}")
    print(f"\n⚠️  Remember to restart your Django server for changes to take effect!")
    print(f"   cd Backend/gymReview && python manage.py runserver\n")


def show_status():
    """Show current dev mode status"""
    is_enabled = get_current_status()
    
    if is_enabled:
        print("\n🔧 Development Mode: ENABLED")
        print("   Current mode: Database-only search (no API calls)")
        print("   To disable: python toggle_dev_mode.py off\n")
    else:
        print("\n🚀 Development Mode: DISABLED")
        print("   Current mode: Google Places API (may incur charges)")
        print("   To enable: python toggle_dev_mode.py on\n")


def main():
    if len(sys.argv) < 2:
        show_status()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['on', 'enable', 'true', '1']:
        set_dev_mode(True)
    elif command in ['off', 'disable', 'false', '0']:
        set_dev_mode(False)
    elif command in ['status', 'show']:
        show_status()
    else:
        print(f"❌ Unknown command: {command}")
        print("\nUsage:")
        print("  python toggle_dev_mode.py on   # Enable dev mode")
        print("  python toggle_dev_mode.py off  # Disable dev mode")
        print("  python toggle_dev_mode.py      # Show current status")
        sys.exit(1)


if __name__ == '__main__':
    main()

