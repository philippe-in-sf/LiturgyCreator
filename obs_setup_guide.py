#!/usr/bin/env python3
"""
OBS Setup Guide and Configuration Helper
Interactive tool to help configure OBS integration with the Liturgical Calendar
"""

import configparser
import json
from typing import Dict, List

def create_custom_config():
    """Interactive configuration creator"""
    print("🕊️ OBS Setup Guide for Liturgical Calendar")
    print("=" * 50)
    print()
    
    config = configparser.ConfigParser()
    
    # OBS Connection Settings
    print("📡 OBS Connection Settings")
    print("-" * 25)
    
    host = input("OBS Host (default: localhost): ").strip() or "localhost"
    port = input("OBS WebSocket Port (default: 4455): ").strip() or "4455"
    password = input("OBS WebSocket Password (leave blank if none): ").strip()
    
    config['OBS'] = {
        'host': host,
        'port': port,
        'password': password
    }
    
    # Scene Mapping Configuration
    print("\n🎬 Scene Mapping Configuration")
    print("-" * 30)
    print("You need to map your OBS scenes and text sources to scripture readings.")
    print("Format: Scene Name : Text Source Name")
    print()
    
    scene_mappings = {}
    
    # Get main scene name
    main_scene = input("What is your main liturgy scene name? (e.g., 'Liturgy', 'Scripture', 'Worship'): ").strip()
    
    if main_scene:
        print(f"\n📖 Text Source Names in '{main_scene}' scene:")
        
        # Scripture readings mappings
        mappings = [
            ("first_reading_text", "First Reading Text", "The main text of the first scripture reading"),
            ("first_reading_reference", "First Reading Reference", "The reference (e.g., 'Genesis 1:1-5')"),
            ("psalm_text", "Psalm Text", "The responsorial psalm text"),
            ("psalm_reference", "Psalm Reference", "The psalm reference (e.g., 'Psalm 23:1-4')"),
            ("second_reading_text", "Second Reading Text", "Second reading text (if applicable)"),
            ("second_reading_reference", "Second Reading Reference", "Second reading reference"),
            ("gospel_text", "Gospel Text", "The Gospel reading text"),
            ("gospel_reference", "Gospel Reference", "The Gospel reference (e.g., 'Matthew 5:1-12')"),
            ("gospel_acclamation", "Gospel Acclamation", "Alleluia or Gospel Acclamation text"),
            ("collect", "Collect Text", "The Prayer of the Day/Collect")
        ]
        
        for key, default_name, description in mappings:
            print(f"\n{description}:")
            source_name = input(f"  Text source name (default: '{default_name}'): ").strip() or default_name
            scene_mappings[key] = f"{main_scene}:{source_name}"
    
    config['SCENE_MAPPING'] = scene_mappings
    
    # Formatting Settings
    print("\n⚙️ Text Formatting Settings")
    print("-" * 26)
    
    max_length = input("Maximum text length per source (default: 500): ").strip() or "500"
    include_verses = input("Include verse numbers? (y/n, default: y): ").strip().lower()
    include_verses = "true" if include_verses in ['y', 'yes', ''] else "false"
    
    config['FORMATTING'] = {
        'max_text_length': max_length,
        'include_verse_numbers': include_verses,
        'line_break_on_verses': 'false'
    }
    
    # API Settings
    config['API'] = {
        'primary_source': 'The Lectionary Page (Episcopal RCL)',
        'base_url': 'https://www.lectionarypage.net',
        'fallback_url': 'https://lectionary.library.vanderbilt.edu',
        'timeout': '10',
        'liturgical_tradition': 'Episcopal',
        'lectionary_cycle': 'Revised Common Lectionary'
    }
    
    # Save configuration
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    
    print("\n✅ Configuration saved to 'config.ini'")
    print("\n📋 Next Steps:")
    print("1. Enable OBS WebSocket Server in OBS Studio (Tools > WebSocket Server Settings)")
    print(f"2. Set WebSocket port to {port} and password if you specified one")
    print("3. Make sure your scene names and text source names match your configuration")
    print("4. Test the connection using the web calendar's 'Send to OBS' button")
    
    return config

def print_example_config():
    """Print example configuration"""
    print("\n📋 Example OBS Setup")
    print("=" * 20)
    print()
    print("Scene Name: 'Liturgy'")
    print("Text Sources in scene:")
    print("  - First Reading Text")
    print("  - First Reading Reference") 
    print("  - Psalm Text")
    print("  - Psalm Reference")
    print("  - Gospel Text")
    print("  - Gospel Reference")
    print("  - Gospel Acclamation")
    print("  - Collect Text")
    print()
    print("This creates a config.ini like:")
    print()
    example_config = """[OBS]
host = localhost
port = 4455
password = 

[SCENE_MAPPING]
first_reading_text = Liturgy:First Reading Text
first_reading_reference = Liturgy:First Reading Reference
psalm_text = Liturgy:Psalm Text
psalm_reference = Liturgy:Psalm Reference
gospel_text = Liturgy:Gospel Text
gospel_reference = Liturgy:Gospel Reference
gospel_acclamation = Liturgy:Gospel Acclamation
collect = Liturgy:Collect Text"""
    
    print(example_config)

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Create custom configuration")
    print("2. See example configuration")
    print("3. Both")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice in ['2', '3']:
        print_example_config()
    
    if choice in ['1', '3']:
        if choice == '3':
            print("\n" + "="*50)
        create_custom_config()