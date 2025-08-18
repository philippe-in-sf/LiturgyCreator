#!/usr/bin/env python3
"""
Run Automation Script
Standalone script to execute the liturgical OBS automation
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

def print_usage():
    """Print usage instructions"""
    print("Daily Liturgical Scripture OBS Automation")
    print("=" * 50)
    print()
    print("This script fetches daily liturgical readings and updates OBS text sources.")
    print()
    print("Prerequisites:")
    print("1. OBS Studio must be running")
    print("2. OBS WebSocket server must be enabled (Tools > WebSocket Server Settings)")
    print("3. Configure 'config.ini' file with your OBS settings and scene mappings")
    print()
    print("Usage:")
    print("  python run_automation.py")
    print()
    print("The script will:")
    print("- Fetch today's liturgical readings")
    print("- Parse scripture references and text")
    print("- Connect to OBS via WebSocket")
    print("- Update configured text sources with scripture content")
    print()

def check_prerequisites():
    """Check if prerequisites are met"""
    issues = []
    
    # Check if config file exists
    if not os.path.exists('config.ini'):
        issues.append("Configuration file 'config.ini' not found")
    
    # Check if required modules can be imported
    try:
        import obsws_python
    except ImportError:
        issues.append("obsws-python module not installed (pip install obsws-python)")
    
    try:
        import requests
    except ImportError:
        issues.append("requests module not installed (pip install requests)")
    
    return issues

def create_sample_config():
    """Create a sample configuration file if none exists"""
    sample_config = """[OBS]
# OBS WebSocket connection settings
host = localhost
port = 4455
password = 

[SCENE_MAPPING]
# Map scripture readings to OBS scenes and text sources
# Format: reading_type = scene_name:text_source_name

# Example mappings - adjust these to match your OBS setup
first_reading_text = Liturgy:First Reading Text
first_reading_reference = Liturgy:First Reading Reference
psalm_text = Liturgy:Psalm Text
psalm_reference = Liturgy:Psalm Reference
gospel_text = Liturgy:Gospel Text
gospel_reference = Liturgy:Gospel Reference

[FORMATTING]
# Text formatting options
max_text_length = 500
include_verse_numbers = true
line_break_on_verses = false

[API]
# Liturgical calendar API settings
base_url = https://calapi.inadiutorium.cz/api/v0/en/calendars/general-en
timeout = 10
"""
    
    try:
        with open('config.ini', 'w') as f:
            f.write(sample_config)
        print("Created sample 'config.ini' file. Please edit it to match your OBS setup.")
        return True
    except Exception as e:
        print(f"Error creating config file: {e}")
        return False

if __name__ == "__main__":
    print_usage()
    
    # Check prerequisites
    issues = check_prerequisites()
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        
        if "config.ini" in str(issues):
            response = input("Would you like to create a sample config.ini file? (y/n): ")
            if response.lower().startswith('y'):
                if create_sample_config():
                    print("Please edit config.ini and run the script again.")
                sys.exit(1)
        
        print("Please resolve these issues and try again.")
        sys.exit(1)
    
    print("Prerequisites checked. Starting automation...")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the main automation
    try:
        success = main()
        if success:
            print("\n✓ Automation completed successfully!")
            print("Check OBS to verify that text sources have been updated.")
        else:
            print("\n✗ Automation completed with errors.")
            print("Check the log file 'liturgy_obs.log' for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nAutomation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("Check the log file 'liturgy_obs.log' for details.")
        sys.exit(1)
