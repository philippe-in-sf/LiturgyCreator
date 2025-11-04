#!/usr/bin/env python3
"""
Find correct URLs for Holy Week feast days on lectionarypage.net
"""

import requests
import time

# Try different URL patterns for Holy Week feast days
url_patterns = {
    'Maundy Thursday': [
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/BMaunThu_RCL.html',
        'https://www.lectionarypage.net/YearABC/HolyWk/MaunThu.html',
        'https://www.lectionarypage.net/YearABC/HolyWk/MaundyThu.html',
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/MaunThu.html',
    ],
    'Good Friday': [
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/BGoodFri_RCL.html',
        'https://www.lectionarypage.net/YearABC/HolyWk/GoodFri.html',
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/GoodFri.html',
    ],
    'Holy Saturday': [
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/BHolySat_RCL.html',
        'https://www.lectionarypage.net/YearABC/HolyWk/HolySat.html',
        'https://www.lectionarypage.net/YearB_RCL/HolyWk/HolySat.html',
    ]
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

print("Testing URLs for Holy Week feast days...")
print("="*60)

for feast_name, urls in url_patterns.items():
    print(f"\n{feast_name}:")
    for url in urls:
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✓ FOUND: {url}")
                break
            else:
                print(f"  ✗ {response.status_code}: {url}")
        except Exception as e:
            print(f"  ✗ ERROR: {url} - {e}")
        time.sleep(0.5)

print("\n" + "="*60)
