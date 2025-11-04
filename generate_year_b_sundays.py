#!/usr/bin/env python3
"""
Generate Year B Sunday dates and URLs for Episcopal Lectionary
Year B: November 29, 2026 - November 21, 2027
Easter 2027: April 12, 2027
"""

import json
from datetime import datetime, timedelta


def calculate_sundays_year_b():
    """Calculate all Sundays in Year B with their celebration names and URLs"""
    
    # Key dates for Year B
    easter_2027 = datetime(2027, 3, 28)  # Easter Day 2027 (CORRECTED from April 12)
    first_advent_2026 = datetime(2026, 11, 29)  # First Sunday of Advent
    christmas_2026 = datetime(2026, 12, 25)
    
    sundays = []
    
    # === ADVENT SEASON (4 Sundays) ===
    advent_sundays = [
        ("2026-11-29", "First Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearB_RCL/Advent/BAdv1_RCL.html"),
        ("2026-12-06", "Second Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearB_RCL/Advent/BAdv2_RCL.html"),
        ("2026-12-13", "Third Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearB_RCL/Advent/BAdv3_RCL.html"),
        ("2026-12-20", "Fourth Sunday of Advent", "Advent", "https://www.lectionarypage.net/YearB_RCL/Advent/BAdv4_RCL.html"),
    ]
    
    # === CHRISTMAS SEASON ===
    christmas_sundays = [
        ("2026-12-27", "First Sunday after Christmas Day", "Christmas", "https://www.lectionarypage.net/YearABC/Christmas/Christmas1.html"),
        ("2027-01-03", "Second Sunday after Christmas Day", "Christmas", "https://www.lectionarypage.net/YearABC/Christmas/Christmas2.html"),
    ]
    
    # === EPIPHANY SEASON ===
    # Epiphany is January 6, 2027 (Wednesday)
    # Sundays after Epiphany until Transfiguration Sunday (last Sunday before Lent)
    
    # Ash Wednesday is 46 days before Easter
    ash_wednesday = easter_2027 - timedelta(days=46)  # February 17, 2027
    # Find the Sunday before Ash Wednesday (Transfiguration)
    transfiguration = ash_wednesday - timedelta(days=(ash_wednesday.weekday() + 1) % 7)
    if transfiguration.weekday() != 6:
        transfiguration = ash_wednesday - timedelta(days=ash_wednesday.weekday() + 1)
    
    epiphany_sundays = [
        ("2027-01-10", "First Sunday after the Epiphany: The Baptism of our Lord", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpi1_RCL.html"),
        ("2027-01-17", "Second Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpi2_RCL.html"),
        ("2027-01-24", "Third Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpi3_RCL.html"),
        ("2027-01-31", "Fourth Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpi4_RCL.html"),
        ("2027-02-07", "Fifth Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpi5_RCL.html"),
        ("2027-02-14", "Last Sunday after the Epiphany", "Epiphany", "https://www.lectionarypage.net/YearB_RCL/Epiphany/BEpiLast_RCL.html"),
    ]
    
    # === LENT SEASON (6 Sundays including Palm Sunday) ===
    # First Sunday in Lent is the first Sunday after Ash Wednesday
    first_lent = ash_wednesday + timedelta(days=(6 - ash_wednesday.weekday()))
    
    lent_sundays = [
        ("2027-02-21", "First Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearB_RCL/Lent/BLent1_RCL.html"),
        ("2027-02-28", "Second Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearB_RCL/Lent/BLent2_RCL.html"),
        ("2027-03-07", "Third Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearB_RCL/Lent/BLent3_RCL.html"),
        ("2027-03-14", "Fourth Sunday in Lent", "Lent", "https://www.lectionarypage.net/YearB_RCL/Lent/BLent4_RCL.html"),
        ("2027-03-21", "Sunday of the Passion: Palm Sunday", "Lent", "https://www.lectionarypage.net/YearB_RCL/HolyWk/BPalmSun_RCL.html"),
    ]
    
    # === EASTER SEASON (7 Sundays including Easter Day through Pentecost) ===
    easter_day = easter_2027
    pentecost = easter_day + timedelta(days=49)  # 7 weeks after Easter
    
    easter_sundays = [
        ("2027-03-28", "Easter Day", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEasterPrin_RCL.html"),
        ("2027-04-04", "Second Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster2_RCL.html"),
        ("2027-04-11", "Third Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster3_RCL.html"),
        ("2027-04-18", "Fourth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster4_RCL.html"),
        ("2027-04-25", "Fifth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster5_RCL.html"),
        ("2027-05-02", "Sixth Sunday of Easter", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster6_RCL.html"),
        ("2027-05-09", "Seventh Sunday of Easter: The Sunday after Ascension Day", "Easter", "https://www.lectionarypage.net/YearB_RCL/Easter/BEaster7_RCL.html"),
        ("2027-05-16", "The Day of Pentecost: Whitsunday", "Easter", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BPentDay_RCL.html"),
    ]
    
    # === SEASON AFTER PENTECOST (Trinity Sunday through Christ the King) ===
    trinity_sunday = pentecost + timedelta(days=7)
    
    pentecost_sundays = [
        ("2027-05-23", "First Sunday after Pentecost: Trinity Sunday", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BTrinity_RCL.html"),
    ]
    
    # Propers start the Sunday after Trinity
    # Proper 4-9 (if they occur before Pentecost season starts)
    # Proper 10-29 cover the rest of the season
    
    propers = [
        ("2027-05-30", "Second Sunday after Pentecost (Proper 4)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp4_RCL.html"),
        ("2027-06-06", "Third Sunday after Pentecost (Proper 5)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp5_RCL.html"),
        ("2027-06-13", "Fourth Sunday after Pentecost (Proper 6)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp6_RCL.html"),
        ("2027-06-20", "Fifth Sunday after Pentecost (Proper 7)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp7_RCL.html"),
        ("2027-06-27", "Sixth Sunday after Pentecost (Proper 8)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp8_RCL.html"),
        ("2027-07-04", "Seventh Sunday after Pentecost (Proper 9)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp9_RCL.html"),
        ("2027-07-11", "Eighth Sunday after Pentecost (Proper 10)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp10_RCL.html"),
        ("2027-07-18", "Ninth Sunday after Pentecost (Proper 11)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp11_RCL.html"),
        ("2027-07-25", "Tenth Sunday after Pentecost (Proper 12)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp12_RCL.html"),
        ("2027-08-01", "Eleventh Sunday after Pentecost (Proper 13)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp13_RCL.html"),
        ("2027-08-08", "Twelfth Sunday after Pentecost (Proper 14)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp14_RCL.html"),
        ("2027-08-15", "Thirteenth Sunday after Pentecost (Proper 15)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp15_RCL.html"),
        ("2027-08-22", "Fourteenth Sunday after Pentecost (Proper 16)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp16_RCL.html"),
        ("2027-08-29", "Fifteenth Sunday after Pentecost (Proper 17)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp17_RCL.html"),
        ("2027-09-05", "Sixteenth Sunday after Pentecost (Proper 18)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp18_RCL.html"),
        ("2027-09-12", "Seventeenth Sunday after Pentecost (Proper 19)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp19_RCL.html"),
        ("2027-09-19", "Eighteenth Sunday after Pentecost (Proper 20)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp20_RCL.html"),
        ("2027-09-26", "Nineteenth Sunday after Pentecost (Proper 21)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp21_RCL.html"),
        ("2027-10-03", "Twentieth Sunday after Pentecost (Proper 22)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp22_RCL.html"),
        ("2027-10-10", "Twenty-first Sunday after Pentecost (Proper 23)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp23_RCL.html"),
        ("2027-10-17", "Twenty-second Sunday after Pentecost (Proper 24)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp24_RCL.html"),
        ("2027-10-24", "Twenty-third Sunday after Pentecost (Proper 25)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp25_RCL.html"),
        ("2027-10-31", "Twenty-fourth Sunday after Pentecost (Proper 26)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp26_RCL.html"),
        ("2027-11-07", "Twenty-fifth Sunday after Pentecost (Proper 27)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp27_RCL.html"),
        ("2027-11-14", "Twenty-sixth Sunday after Pentecost (Proper 28)", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp28_RCL.html"),
        ("2027-11-21", "Last Sunday after Pentecost: Christ the King", "Pentecost", "https://www.lectionarypage.net/YearB_RCL/Pentecost/BProp29_RCL.html"),
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
    """Generate and save Year B Sundays to JSON"""
    print("Generating Year B Sunday dates and URLs...")
    
    sundays = calculate_sundays_year_b()
    
    print(f"\nTotal Sundays in Year B: {len(sundays)}")
    print(f"Date range: {sundays[0]['date']} to {sundays[-1]['date']}")
    
    # Save to JSON file
    output_file = "year_b_sundays.json"
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
    
    # Verify all URLs contain YearB_RCL or YearABC (for Christmas)
    non_year_b = [s for s in sundays if 'YearB_RCL' not in s['url'] and 'YearABC' not in s['url']]
    if non_year_b:
        print(f"\nWARNING: {len(non_year_b)} URLs do not contain 'YearB_RCL' or 'YearABC'!")
        for s in non_year_b:
            print(f"  {s['date']}: {s['url']}")
    else:
        print("\n✓ All URLs verified to contain 'YearB_RCL' or 'YearABC' (Episcopal RCL)")


if __name__ == '__main__':
    main()
