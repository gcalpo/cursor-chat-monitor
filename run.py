#!/usr/bin/env python3
"""
Cursor Chat Monitor - Simple Run Script (Python Version)
This script handles all the venv setup and runs the app for you.
Works on all platforms (macOS, Windows, Linux).

Usage: python3 run.py [options...]
Example: python3 run.py --debug --interval-ms=2000
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_colored(text, color='blue'):
    """Print colored text to terminal"""
    colors = {
        'red': '\033[0;31m',
        'green': '\033[0;32m',
        'yellow': '\033[1;33m',
        'blue': '\033[0;34m',
        'nc': '\033[0m'  # No Color
    }
    
    # On Windows, don't use colors unless we're in a modern terminal
    if platform.system() == 'Windows':
        print(text)
    else:
        color_code = colors.get(color, colors['blue'])
        print(f"{color_code}{text}{colors['nc']}")

def run_command(cmd, shell=False, capture_output=False, silent=False):
    """Run a command and handle errors"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            if silent:
                result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(cmd, shell=shell, check=True)
            return True
    except subprocess.CalledProcessError as e:
        if not silent:
            print_colored(f"❌ Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}", 'red')
            if capture_output and e.stderr:
                print_colored(f"Error: {e.stderr}", 'red')
        return False
    except FileNotFoundError:
        print_colored(f"❌ Command not found: {cmd[0] if isinstance(cmd, list) else cmd}", 'red')
        return False

def main():
    """Main entry point"""
    print_colored("🚀 Cursor Chat Monitor - Simple Run Script", 'blue')
    print_colored("═══════════════════════════════════════════", 'blue')
    
    # Get script directory and change to it
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_colored(f"🐍 Found Python {python_version}", 'green')
    
    # Determine the correct Python executable
    python_cmd = sys.executable
    if not python_cmd:
        python_cmd = 'python3' if platform.system() != 'Windows' else 'python'
    
    # Check if we can run Python
    if not run_command([python_cmd, '--version'], capture_output=True, silent=True):
        print_colored("❌ Python is not available or not working correctly", 'red')
        sys.exit(1)
    
    # Create virtual environment if it doesn't exist
    venv_path = script_dir / 'venv'
    if not venv_path.exists():
        print_colored("📦 Creating virtual environment...", 'yellow')
        if not run_command([python_cmd, '-m', 'venv', 'venv']):
            print_colored("❌ Failed to create virtual environment", 'red')
            sys.exit(1)
        print_colored("✅ Virtual environment created", 'green')
    else:
        print_colored("📦 Virtual environment already exists", 'green')
    
    # Determine the correct pip executable in the virtual environment
    if platform.system() == 'Windows':
        venv_python = venv_path / 'Scripts' / 'python.exe'
        venv_pip = venv_path / 'Scripts' / 'pip.exe'
    else:
        venv_python = venv_path / 'bin' / 'python'
        venv_pip = venv_path / 'bin' / 'pip'
    
    # Activate virtual environment by using the venv's Python directly
    print_colored("🔌 Using virtual environment...", 'yellow')
    
    # Upgrade pip
    print_colored("⬆️  Upgrading pip...", 'yellow')
    run_command([str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'], silent=True)
    
    # Install/upgrade dependencies
    print_colored("📚 Installing/upgrading dependencies...", 'yellow')
    if not run_command([str(venv_pip), 'install', '-r', 'requirements.txt'], silent=True):
        print_colored("❌ Failed to install dependencies", 'red')
        sys.exit(1)
    print_colored("✅ Dependencies installed", 'green')
    
    # Check if the main script exists
    main_script = script_dir / 'cursor_chat_monitor.py'
    if not main_script.exists():
        print_colored("❌ cursor_chat_monitor.py not found", 'red')
        print_colored("Make sure you're running this script from the project root directory", 'yellow')
        sys.exit(1)
    
    print_colored("🎯 Starting Cursor Chat Monitor...", 'green')
    print_colored("═══════════════════════════════════════════", 'blue')
    
    # Pass all arguments to the main script
    cmd = [str(venv_python), 'cursor_chat_monitor.py'] + sys.argv[1:]
    
    try:
        # Run the main application
        subprocess.run(cmd, check=False)  # Don't check return code, let the app handle its own exit
    except KeyboardInterrupt:
        print_colored("\n👋 Goodbye!", 'yellow')
    except Exception as e:
        print_colored(f"❌ Error running application: {e}", 'red')
        sys.exit(1)

if __name__ == '__main__':
    main() 