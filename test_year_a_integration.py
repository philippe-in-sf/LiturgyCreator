#!/usr/bin/env python3
"""
Test Year A Integration with Liturgy Fetcher
Verifies that Year A and Year C readings load correctly
"""

from datetime import datetime
from liturgy_fetcher import LiturgyFetcher


def test_readings():
    """Test Year A and Year C readings"""
    print("=" * 60)
    print("Testing Year A Integration")
    print("=" * 60)
    
    fetcher = LiturgyFetcher()
    
    # Test 1: First Sunday of Advent (Year A - Nov 30, 2025)
    print("\n[Test 1] First Sunday of Advent - Nov 30, 2025 (Year A)")
    date1 = datetime(2025, 11, 30)
    readings1 = fetcher.fetch_daily_readings(date1, 'eucharist')
    
    if readings1:
        print(f"✓ Loaded readings for {date1.strftime('%Y-%m-%d')}")
        print(f"  Celebration: {readings1.get('celebration', 'N/A')}")
        print(f"  Liturgical Year: {readings1.get('liturgical_year', 'N/A')}")
        print(f"  Source: {readings1.get('source', 'N/A')}")
        print(f"  First Reading: {readings1['readings']['first_reading']['reference']}")
        print(f"  Gospel: {readings1['readings']['gospel']['reference']}")
        if readings1['readings']['collect']['reference']:
            print(f"  Collect: {readings1['readings']['collect']['reference']}")
    else:
        print(f"✗ FAILED to load readings for {date1.strftime('%Y-%m-%d')}")
    
    # Test 2: Easter Day (Year A - April 12, 2026)
    print("\n[Test 2] Easter Day - April 12, 2026 (Year A)")
    date2 = datetime(2026, 4, 12)
    readings2 = fetcher.fetch_daily_readings(date2, 'eucharist')
    
    if readings2:
        print(f"✓ Loaded readings for {date2.strftime('%Y-%m-%d')}")
        print(f"  Celebration: {readings2.get('celebration', 'N/A')}")
        print(f"  Liturgical Year: {readings2.get('liturgical_year', 'N/A')}")
        print(f"  Source: {readings2.get('source', 'N/A')}")
        print(f"  First Reading: {readings2['readings']['first_reading']['reference']}")
        print(f"  Gospel: {readings2['readings']['gospel']['reference']}")
        if readings2['readings']['collect']['reference']:
            print(f"  Collect: {readings2['readings']['collect']['reference']}")
    else:
        print(f"✗ FAILED to load readings for {date2.strftime('%Y-%m-%d')}")
    
    # Test 3: Existing Year C reading (Aug 17, 2025)
    print("\n[Test 3] Tenth Sunday after Pentecost - Aug 17, 2025 (Year C)")
    date3 = datetime(2025, 8, 17)
    readings3 = fetcher.fetch_daily_readings(date3, 'eucharist')
    
    if readings3:
        print(f"✓ Loaded readings for {date3.strftime('%Y-%m-%d')}")
        print(f"  Celebration: {readings3.get('celebration', 'N/A')}")
        print(f"  Liturgical Year: {readings3.get('liturgical_year', 'N/A')}")
        print(f"  Source: {readings3.get('source', 'N/A')}")
        print(f"  First Reading: {readings3['readings']['first_reading']['reference']}")
        print(f"  Gospel: {readings3['readings']['gospel']['reference']}")
        if readings3['readings']['collect']['reference']:
            print(f"  Collect: {readings3['readings']['collect']['reference']}")
    else:
        print(f"✗ FAILED to load readings for {date3.strftime('%Y-%m-%d')}")
    
    # Test 4: Another Year A reading (Christmas, Dec 28, 2025)
    print("\n[Test 4] First Sunday after Christmas - Dec 28, 2025 (Year A)")
    date4 = datetime(2025, 12, 28)
    readings4 = fetcher.fetch_daily_readings(date4, 'eucharist')
    
    if readings4:
        print(f"✓ Loaded readings for {date4.strftime('%Y-%m-%d')}")
        print(f"  Celebration: {readings4.get('celebration', 'N/A')}")
        print(f"  Liturgical Year: {readings4.get('liturgical_year', 'N/A')}")
        print(f"  Source: {readings4.get('source', 'N/A')}")
        print(f"  First Reading: {readings4['readings']['first_reading']['reference']}")
        print(f"  Gospel: {readings4['readings']['gospel']['reference']}")
    else:
        print(f"✗ FAILED to load readings for {date4.strftime('%Y-%m-%d')}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    success_count = sum([
        bool(readings1),
        bool(readings2),
        bool(readings3),
        bool(readings4)
    ])
    print(f"Tests Passed: {success_count}/4")
    
    if success_count == 4:
        print("✓ ALL TESTS PASSED!")
        print("✓ Year A integration successful")
        print("✓ Year C backward compatibility maintained")
    else:
        print("✗ SOME TESTS FAILED")
    
    return success_count == 4


if __name__ == '__main__':
    success = test_readings()
    exit(0 if success else 1)
