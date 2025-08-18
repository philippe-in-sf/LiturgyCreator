#!/usr/bin/env python3
"""
Demo script to show Episcopal liturgical readings being fetched
"""

import sys
from datetime import datetime
from liturgy_fetcher import LiturgyFetcher
from scripture_parser import ScriptureParser

def main():
    print("Episcopal Church Liturgical Readings Demo")
    print("=" * 50)
    print()
    
    # Initialize components
    liturgy_fetcher = LiturgyFetcher()
    scripture_parser = ScriptureParser()
    
    # Get current date
    current_date = datetime.now()
    print(f"Fetching Episcopal readings for: {current_date.strftime('%A, %B %d, %Y')}")
    print()
    
    # Fetch liturgical data
    liturgical_data = liturgy_fetcher.fetch_daily_readings(current_date)
    
    if not liturgical_data:
        print("❌ Failed to fetch liturgical data")
        return
    
    print(f"✓ Successfully fetched readings from: {liturgical_data.get('source', 'Unknown')}")
    print(f"📅 Liturgical celebration: {liturgical_data.get('celebration', 'Unknown')}")
    print(f"🔄 Liturgical year: {liturgical_data.get('liturgical_year', 'Unknown')}")
    print()
    
    # Parse scripture data
    parsed_scriptures = scripture_parser.parse_readings(liturgical_data)
    
    if not parsed_scriptures:
        print("❌ Failed to parse scripture readings")
        return
    
    print(f"✓ Successfully parsed {len(parsed_scriptures)} readings")
    print()
    
    # Display each reading
    for reading_type, reading_data in parsed_scriptures.items():
        print(f"📖 {reading_type.replace('_', ' ').title()}")
        print(f"   Reference: {reading_data.get('reference', 'N/A')}")
        text = reading_data.get('text', 'N/A')
        # Truncate long text for display
        if len(text) > 200:
            text = text[:200] + "..."
        print(f"   Text: {text}")
        print()
    
    # Show how it would be passed to OBS
    print("🎬 OBS Variables that would be set:")
    print("-" * 40)
    
    variables = scripture_parser.get_reading_variables(parsed_scriptures)
    for var_name, var_value in variables.items():
        # Show just reference for brevity
        if 'text' in var_name:
            display_value = var_value[:100] + "..." if len(var_value) > 100 else var_value
        else:
            display_value = var_value
        print(f"   {var_name}: {display_value}")
    
    print()
    print("✓ Demo completed successfully!")
    print("This is the data that would be sent to your OBS text sources.")

if __name__ == "__main__":
    main()