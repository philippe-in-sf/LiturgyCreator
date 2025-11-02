#!/usr/bin/env python3
"""
Generate Year A Sunday dates and URLs for Episcopal Lectionary
Year A: November 30, 2025 - November 22, 2026
Easter 2026: April 12, 2026
"""

import json
from datetime import datetime, timedelta


def calculate_sundays_year_a():
    """Calculate all Sundays in Year A with their celebration names and URLs"""
    
    # Key dates for Year A
    easter_2026 = datetime(2026, 4, 12)  # Easter Day 2026
    first_advent_2025 = datetime(2025, 11, 30)  # First Sunday of Advent
    christmas_2025 = datetime(2025, 12, 25)
    
    sundays = []
    
    # === ADVENT SEASON (4 Sundays) ===
    advent_sundays = [
        ("2025-11-30", "First Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearA_RCL/Advent/AAdv1_RCL.html"),
        ("2025-12-07", "Second Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearA_RCL/Advent/AAdv2_RCL.html"),
        ("2025-12-14", "Third Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearA_RCL/Advent/AAdv3_RCL.html"),
        ("2025-12-21", "Fourth Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearA_RCL/Advent/AAdv4_RCL.html"),
    ]
    
    # === CHRISTMAS SEASON ===
    christmas_sundays = [
        ("2025-12-28", "First Sunday after Christmas Day", "Christmas", "https://www.lectionarypage.net/YearABC/Christmas/Christmas1.html"),
        ("2026-01-04", "Second Sunday after Christmas Day", "Christmas", "https://www.lectionarypage.net/YearABC/Christmas/Christmas2.html"),
    ]
    
    # === EPIPHANY SEASON ===
    # Epiphany is January 6, 2026 (Tuesday)
    # Sundays after Epiphany until Transfiguration Sunday (last Sunday before Lent)
    
    # Ash Wednesday is 46 days before Easter
    ash_wednesday = easter_2026 - timedelta(days=46)  # February 25, 2026
    # Find the Sunday before Ash Wednesday (Transfiguration)
    transfiguration = ash_wednesday - timedelta(days=(ash_wednesday.weekday() + 1) % 7)
    if transfiguration.weekday() != 6:
        transfiguration = ash_wednesday - timedelta(days=ash_wednesday.weekday() + 1)
    
    epiphany_sundays = [
        ("2026-01-11", "First Sunday after the Epiphany: The Baptism of our Lord", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi1_RCL.html"),
        ("2026-01-18", "Second Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi2_RCL.html"),
        ("2026-01-25", "Third Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi3_RCL.html"),
        ("2026-02-01", "Fourth Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi4_RCL.html"),
        ("2026-02-08", "Fifth Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi5_RCL.html"),
        ("2026-02-15", "Sixth Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpi6_RCL.html"),
        ("2026-02-22", "Last Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearA_RCL/Epiphany/AEpiLast_RCL.html"),
    ]
    
    # === LENT SEASON (6 Sundays including Palm Sunday) ===
    # First Sunday in Lent is the first Sunday after Ash Wednesday
    first_lent = ash_wednesday + timedelta(days=(6 - ash_wednesday.weekday()))
    
    lent_sundays = [
        ("2026-03-01", "First Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearA_RCL/Lent/ALent1_RCL.html"),
        ("2026-03-08", "Second Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearA_RCL/Lent/ALent2_RCL.html"),
        ("2026-03-15", "Third Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearA_RCL/Lent/ALent3_RCL.html"),
        ("2026-03-22", "Fourth Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearA_RCL/Lent/ALent4_RCL.html"),
        ("2026-03-29", "Fifth Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearA_RCL/Lent/ALent5_RCL.html"),
        ("2026-04-05", "Sunday of the Passion: Palm Sunday", "Lent", "https://www.lectionarypage.net/YearA_RCL/HolyWk/APalmSun_RCL.html"),
    ]
    
    # === EASTER SEASON (7 Sundays including Easter Day through Pentecost) ===
    easter_day = easter_2026
    pentecost = easter_day + timedelta(days=49)  # 7 weeks after Easter
    
    easter_sundays = [
        ("2026-04-12", "Easter Day", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEasterPrin_RCL.html"),
        ("2026-04-19", "Second Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster2_RCL.html"),
        ("2026-04-26", "Third Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster3_RCL.html"),
        ("2026-05-03", "Fourth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster4_RCL.html"),
        ("2026-05-10", "Fifth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster5_RCL.html"),
        ("2026-05-17", "Sixth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster6_RCL.html"),
        ("2026-05-24", "Seventh Sunday of Easter: The Sunday after Ascension Day", "Easter", "https://www.lectionarypage.net/YearA_RCL/Easter/AEaster7_RCL.html"),
        ("2026-05-31", "The Day of Pentecost: Whitsunday", "Easter", "https://www.lectionarypage.net/YearA_RCL/Pentecost/APentDay_RCL.html"),
    ]
    
    # === SEASON AFTER PENTECOST (Trinity Sunday through Christ the King) ===
    trinity_sunday = pentecost + timedelta(days=7)
    
    pentecost_sundays = [
        ("2026-06-07", "First Sunday after Pentecost: Trinity Sunday", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/ATrinity_RCL.html"),
    ]
    
    # Propers start the Sunday after Trinity
    # Proper 4-9 (if they occur before Pentecost season starts)
    # Proper 10-29 cover the rest of the season
    
    propers = [
        ("2026-06-14", "Second Sunday after Pentecost (Proper 6)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp6_RCL.html"),
        ("2026-06-21", "Third Sunday after Pentecost (Proper 7)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp7_RCL.html"),
        ("2026-06-28", "Fourth Sunday after Pentecost (Proper 8)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/Aprop8_RCL.html"),
        ("2026-07-05", "Fifth Sunday after Pentecost (Proper 9)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp9_RCL.html"),
        ("2026-07-12", "Sixth Sunday after Pentecost (Proper 10)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp10_RCL.html"),
        ("2026-07-19", "Seventh Sunday after Pentecost (Proper 11)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp11_RCL.html"),
        ("2026-07-26", "Eighth Sunday after Pentecost (Proper 12)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp12_RCL.html"),
        ("2026-08-02", "Ninth Sunday after Pentecost (Proper 13)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp13_RCL.html"),
        ("2026-08-09", "Tenth Sunday after Pentecost (Proper 14)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp14_RCL.html"),
        ("2026-08-16", "Eleventh Sunday after Pentecost (Proper 15)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp15_RCL.html"),
        ("2026-08-23", "Twelfth Sunday after Pentecost (Proper 16)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp16_RCL.html"),
        ("2026-08-30", "Thirteenth Sunday after Pentecost (Proper 17)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp17_RCL.html"),
        ("2026-09-06", "Fourteenth Sunday after Pentecost (Proper 18)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp18_RCL.html"),
        ("2026-09-13", "Fifteenth Sunday after Pentecost (Proper 19)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp19_RCL.html"),
        ("2026-09-20", "Sixteenth Sunday after Pentecost (Proper 20)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp20_RCL.html"),
        ("2026-09-27", "Seventeenth Sunday after Pentecost (Proper 21)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp21_RCL.html"),
        ("2026-10-04", "Eighteenth Sunday after Pentecost (Proper 22)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp22_RCL.html"),
        ("2026-10-11", "Nineteenth Sunday after Pentecost (Proper 23)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp23_RCL.html"),
        ("2026-10-18", "Twentieth Sunday after Pentecost (Proper 24)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp24_RCL.html"),
        ("2026-10-25", "Twenty-first Sunday after Pentecost (Proper 25)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp25_RCL.html"),
        ("2026-11-01", "Twenty-second Sunday after Pentecost (Proper 26)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp26_RCL.html"),
        ("2026-11-08", "Twenty-third Sunday after Pentecost (Proper 27)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp27_RCL.html"),
        ("2026-11-15", "Twenty-fourth Sunday after Pentecost (Proper 28)", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp28_RCL.html"),
        ("2026-11-22", "Last Sunday after Pentecost: Christ the King", "Pentecost", "https://www.lectionarypage.net/YearA_RCL/Pentecost/AProp29_RCL.html"),
    ]
    
    # Combine all Sundays
    all_sundays = (
        advent_sundays +
        christmas_sundays +
        epiphany_sundays +
        lent_sundays +
        easter_sundays +
        pentecost_sundays +
        propers
    )
    
    # Convert to structured format
    for date_str, celebration, season, url in all_sundays:
        sundays.append({
            "date": date_str,
            "celebration_name": celebration,
            "season": season,
            "url": url
        })
    
    return sundays


def main():
    """Generate and save Year A Sundays to JSON"""
    print("Generating Year A Sunday dates and URLs...")
    
    sundays = calculate_sundays_year_a()
    
    print(f"\nTotal Sundays in Year A: {len(sundays)}")
    print(f"Date range: {sundays[0]['date']} to {sundays[-1]['date']}")
    
    # Save to JSON file
    output_file = "year_a_sundays.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sundays, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to {output_file}")
    
    # Display first few and last few
    print("\n=== First 5 Sundays ===")
    for sunday in sundays[:5]:
        print(f"{sunday['date']}: {sunday['celebration_name']}")
        print(f"  URL: {sunday['url']}")
    
    print("\n=== Last 5 Sundays ===")
    for sunday in sundays[-5:]:
        print(f"{sunday['date']}: {sunday['celebration_name']}")
        print(f"  URL: {sunday['url']}")
    
    # Verify all URLs contain YearA_RCL
    non_year_a = [s for s in sundays if 'YearA_RCL' not in s['url']]
    if non_year_a:
        print(f"\nWARNING: {len(non_year_a)} URLs do not contain 'YearA_RCL'!")
        for s in non_year_a:
            print(f"  {s['date']}: {s['url']}")
    else:
        print("\n✓ All URLs verified to contain 'YearA_RCL' (Episcopal RCL)")


if __name__ == '__main__':
    main()
