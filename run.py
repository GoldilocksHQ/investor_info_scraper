#!/usr/bin/env python
"""
Main entry point for the investor profile parser.

This script provides a command-line interface to the various
functionalities of the investor profile parser.

Usage:
    python run.py [command]

Commands:
    process  - Process all investor profiles in data/html
    profile  - Parse a single investor profile
    display  - Display investor data
    help     - Show this help message

Examples:
    python run.py process
    python run.py profile data/html/investors-rick-thompson.html
    python run.py display
"""
import os
import sys
import argparse
import importlib.util

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

def import_script(script_path):
    """Dynamically import a Python script."""
    spec = importlib.util.spec_from_file_location("module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs('data/html', exist_ok=True)
    os.makedirs('data/output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Investor Profile Parser")
    parser.add_argument('command', choices=['process', 'profile', 'display', 'help'],
                        help="Command to execute")
    parser.add_argument('args', nargs='*', 
                        help="Additional arguments for the command")
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Process command
    if args.command == 'help':
        print(__doc__)
        return
    
    # Map of commands to script files
    scripts = {
        'process': 'src/investor_parser/scripts/batch_process.py',
        'profile': 'src/investor_parser/scripts/parse_profile.py',
        'display': 'src/investor_parser/scripts/display_data.py'
    }
    
    # Check if the script exists
    script_path = scripts.get(args.command)
    if not script_path or not os.path.exists(script_path):
        print(f"Error: Script for command '{args.command}' not found.")
        return
    
    # Set sys.argv for the imported script
    sys.argv = [script_path] + args.args
    
    # Import and run the script
    script = import_script(script_path)
    script.main()

if __name__ == "__main__":
    main() 