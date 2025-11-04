#!/usr/bin/env python3
"""
Validate Year B readings and check for completeness
"""

import json
from datetime import datetime


def validate_year_b_readings():
    """Validate Year B readings file"""
    
    # Load the data
    with open('year_b_readings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year_b = data.get('YearB', {})
    
    print("="*60)
    print("Year B Readings Validation")
    print("="*60)
    
    # Check total number of entries
    print(f"\nTotal entries: {len(year_b)}")
    
    # Check date range
    dates = sorted(year_b.keys())
    print(f"Date range: {dates[0]} to {dates[-1]}")
    
    # Expected key feast days and Sundays
    expected_dates = {
        # Advent
        "2026-11-29": "First Sunday of Advent",
        "2026-12-06": "Second Sunday of Advent",
        "2026-12-13": "Third Sunday of Advent (Gaudete Sunday)",
        "2026-12-20": "Fourth Sunday of Advent",
        
        # Christmas Season
        "2026-12-27": "First Sunday after Christmas",
        
        # Epiphany Season
        "2027-01-10": "First Sunday after Epiphany (Baptism of our Lord)",
        "2027-02-14": "Last Sunday after Epiphany (Transfiguration)",
        
        # Lent
        "2027-02-21": "First Sunday in Lent",
        "2027-03-28": "Palm Sunday",
        
        # Easter
        "2027-04-12": "Easter Day",
        "2027-04-19": "Second Sunday of Easter",
        
        # Pentecost
        "2027-05-31": "Day of Pentecost",
        "2027-06-07": "Trinity Sunday",
        
        # End of Year
        "2027-11-21": "Christ the King",
    }
    
    print("\n" + "="*60)
    print("Checking Key Dates")
    print("="*60)
    
    missing_dates = []
    for date_str, celebration in expected_dates.items():
        if date_str in year_b:
            print(f"✓ {date_str}: {celebration}")
        else:
            print(f"✗ MISSING: {date_str}: {celebration}")
            missing_dates.append(date_str)
    
    # Check each entry for completeness
    print("\n" + "="*60)
    print("Checking Reading Completeness")
    print("="*60)
    
    incomplete_entries = []
    empty_readings = []
    
    for date_str in sorted(year_b.keys()):
        readings = year_b[date_str]
        
        # Check if all required fields are present
        required_fields = ['first_reading', 'psalm', 'second_reading', 'gospel', 'collect']
        missing_fields = [field for field in required_fields if field not in readings]
        
        if missing_fields:
            incomplete_entries.append((date_str, missing_fields))
            continue
        
        # Check if readings have both reference and text
        empty_count = 0
        for field in required_fields:
            reading = readings[field]
            if not reading.get('reference') and not reading.get('text'):
                empty_count += 1
        
        if empty_count > 0:
            empty_readings.append((date_str, empty_count))
    
    if incomplete_entries:
        print(f"\n⚠ Found {len(incomplete_entries)} entries with missing fields:")
        for date_str, missing in incomplete_entries[:5]:  # Show first 5
            print(f"  {date_str}: Missing {missing}")
    else:
        print("✓ All entries have required fields")
    
    if empty_readings:
        print(f"\n⚠ Found {len(empty_readings)} entries with empty readings:")
        for date_str, count in empty_readings[:5]:  # Show first 5
            print(f"  {date_str}: {count} empty reading(s)")
    else:
        print("✓ All entries have content in readings")
    
    # Sample a few entries to show structure
    print("\n" + "="*60)
    print("Sample Entries")
    print("="*60)
    
    sample_dates = [dates[0], dates[len(dates)//2], dates[-1]]
    for date_str in sample_dates:
        readings = year_b[date_str]
        print(f"\n{date_str}:")
        print(f"  First Reading: {readings['first_reading']['reference']}")
        print(f"  Psalm: {readings['psalm']['reference']}")
        print(f"  Second Reading: {readings['second_reading']['reference']}")
        print(f"  Gospel: {readings['gospel']['reference']}")
        print(f"  Collect: {readings['collect']['reference']}")
    
    # Statistics
    print("\n" + "="*60)
    print("Statistics")
    print("="*60)
    
    total_readings = 0
    for readings in year_b.values():
        for field in ['first_reading', 'psalm', 'second_reading', 'gospel', 'collect']:
            if readings[field].get('reference') or readings[field].get('text'):
                total_readings += 1
    
    print(f"Total readings with content: {total_readings}")
    print(f"Average readings per entry: {total_readings / len(year_b):.1f}")
    
    # Final verdict
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if not missing_dates and not incomplete_entries and not empty_readings:
        print("✓ PASS: All validation checks passed!")
        print(f"✓ {len(year_b)} entries successfully validated")
        print(f"✓ {total_readings} total readings")
        return True
    else:
        print("⚠ NEEDS ATTENTION:")
        if missing_dates:
            print(f"  - {len(missing_dates)} expected dates missing")
        if incomplete_entries:
            print(f"  - {len(incomplete_entries)} entries with missing fields")
        if empty_readings:
            print(f"  - {len(empty_readings)} entries with empty readings")
        return False


if __name__ == '__main__':
    validate_year_b_readings()
