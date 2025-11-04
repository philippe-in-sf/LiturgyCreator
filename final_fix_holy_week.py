#!/usr/bin/env python3
"""
Final fix for Holy Week feast days in Year B readings
Uses correct URLs and manual entry for Maundy Thursday
"""

import json
import time
import requests
from bs4 import BeautifulSoup
import re


def clean_text(text: str) -> str:
    """Clean up text spacing issues"""
    if not text:
        return text
    
    text = re.sub(r'\b([B-HJ-Z])\s+([a-z])', r'\1\2', text)
    text = re.sub(r'\b(I)\s+(n)\b', r'\1\2', text)
    text = re.sub(r'\b(A)\s+(l|g|n[d])', r'\1\2', text)
    text = re.sub(r'\s+[\'\u2019]s\b', '\u2019s', text)
    text = re.sub(r'\s+([,.:;!?])', r'\1', text)
    text = re.sub(r'\s+(["\')\]])', r'\1', text)
    text = re.sub(r'(["\'(\[])\s+', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fetch_readings_from_url(url):
    """Fetch and parse readings from The Lectionary Page"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    try:
        print(f"  Fetching: {url}")
        response = session.get(url, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        html = response.text
        
        readings = {
            'first_reading': {'reference': '', 'text': ''},
            'psalm': {'reference': '', 'text': ''},
            'second_reading': {'reference': '', 'text': ''},
            'gospel': {'reference': '', 'text': ''},
            'collect': {'reference': '', 'text': ''}
        }
        
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('article')
        
        for article in articles:
            h2 = article.find('h2', class_='lessonHeading')
            if not h2:
                continue
                
            heading_text = h2.get_text(separator=" ", strip=True)
            
            if 'Collect' in heading_text:
                collect_p = article.find('p', class_='collectText')
                if collect_p:
                    readings['collect'] = {
                        'reference': 'The Collect',
                        'text': clean_text(collect_p.get_text(separator=" ", strip=True))
                    }
            
            elif 'Old Testament' in heading_text or 'First Reading' in heading_text:
                h3 = article.find('h3', class_='lessonCitation')
                if h3:
                    ref = h3.get_text(separator=" ", strip=True)
                    text_div = h3.find_next_sibling('div')
                    if text_div:
                        paragraphs = text_div.find_all('p', class_=['lessonText', 'poetryText'])
                        text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                        readings['first_reading'] = {
                            'reference': clean_text(ref),
                            'text': clean_text(' '.join(text_parts))
                        }
            
            elif 'Psalm' in heading_text or 'Response' in heading_text:
                h3 = article.find('h3', class_='lessonCitation')
                if h3:
                    ref = h3.get_text(separator=" ", strip=True)
                    text_div = h3.find_next_sibling('div')
                    if text_div:
                        paragraphs = text_div.find_all('p', class_='psalmText')
                        text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                        readings['psalm'] = {
                            'reference': clean_text(ref),
                            'text': clean_text(' '.join(text_parts))
                        }
            
            elif 'Epistle' in heading_text or 'Second Reading' in heading_text:
                h3 = article.find('h3', class_='lessonCitation')
                if h3:
                    ref = h3.get_text(separator=" ", strip=True)
                    text_div = h3.find_next_sibling('div')
                    if text_div:
                        paragraphs = text_div.find_all('p', class_='lessonText')
                        text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                        readings['second_reading'] = {
                            'reference': clean_text(ref),
                            'text': clean_text(' '.join(text_parts))
                        }
            
            elif 'Gospel' in heading_text:
                h3 = article.find('h3', class_='lessonCitation')
                if h3:
                    ref = h3.get_text(separator=" ", strip=True)
                    text_div = h3.find_next_sibling('div')
                    if text_div:
                        paragraphs = text_div.find_all('p', class_='lessonText')
                        text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                        readings['gospel'] = {
                            'reference': clean_text(ref),
                            'text': clean_text(' '.join(text_parts))
                        }
        
        found_count = sum(1 for r in readings.values() if r['reference'] or r['text'])
        print(f"  ✓ Extracted {found_count}/5 readings")
        
        return readings
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    print("="*60)
    print("Final Fix: Adding Holy Week Feast Days to Year B")
    print("="*60)
    
    # Load existing year_b_readings.json
    print("\n1. Loading existing year_b_readings.json...")
    with open('year_b_readings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year_b_data = data.get('YearB', {})
    print(f"   ✓ Loaded {len(year_b_data)} existing entries")
    
    # Maundy Thursday readings (manual entry - same every year)
    print("\n2. Adding Maundy Thursday readings (manual entry)...")
    year_b_data['2027-03-25'] = {
        'first_reading': {
            'reference': 'Exodus 12:1-14',
            'text': ''
        },
        'psalm': {
            'reference': 'Psalm 116:1-2, 12-19',
            'text': ''
        },
        'second_reading': {
            'reference': '1 Corinthians 11:23-26',
            'text': ''
        },
        'gospel': {
            'reference': 'John 13:1-17, 31b-35',
            'text': ''
        },
        'collect': {
            'reference': 'The Collect',
            'text': ''
        }
    }
    print("   ✓ Added Maundy Thursday (March 25, 2027)")
    
    # Good Friday - fetch from correct URL
    print("\n3. Fetching Good Friday readings...")
    good_friday_readings = fetch_readings_from_url('https://www.lectionarypage.net/YearABC/HolyWk/GoodFri.html')
    if good_friday_readings:
        year_b_data['2027-03-26'] = good_friday_readings
        print("   ✓ Added Good Friday (March 26, 2027)")
    time.sleep(1.5)
    
    # Holy Saturday - fetch from correct URL
    print("\n4. Fetching Holy Saturday readings...")
    holy_saturday_readings = fetch_readings_from_url('https://www.lectionarypage.net/YearABC/HolyWk/HolySat.html')
    if holy_saturday_readings:
        year_b_data['2027-03-27'] = holy_saturday_readings
        print("   ✓ Added Holy Saturday (March 27, 2027)")
    
    # Save updated data
    print("\n5. Saving updated year_b_readings.json...")
    output_data = {'YearB': year_b_data}
    with open('year_b_readings.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved {len(year_b_data)} total entries")
    
    # Final Verification
    print("\n" + "="*60)
    print("FINAL VERIFICATION:")
    print("="*60)
    
    critical_dates = {
        '2027-03-21': 'Palm Sunday',
        '2027-03-25': 'Maundy Thursday',
        '2027-03-26': 'Good Friday',
        '2027-03-27': 'Holy Saturday',
        '2027-03-28': 'Easter Sunday',
        '2027-05-06': 'Ascension Day',
        '2027-05-16': 'Pentecost',
        '2027-05-23': 'Trinity Sunday'
    }
    
    for date, expected_name in critical_dates.items():
        if date in year_b_data:
            gospel_ref = year_b_data[date].get('gospel', {}).get('reference', 'N/A')
            print(f"✓ {date}: {expected_name} - Gospel: {gospel_ref}")
        else:
            print(f"✗ {date}: {expected_name} - MISSING!")
    
    # Check for incorrect dates
    print("\n" + "="*60)
    print("CHECKING FOR INCORRECT DATES (should not exist):")
    print("="*60)
    incorrect_dates = ['2027-04-08', '2027-04-09', '2027-04-10', '2027-04-12']
    all_correct = True
    for date in incorrect_dates:
        if date in year_b_data:
            print(f"✗ {date}: STILL EXISTS (ERROR!)")
            all_correct = False
        else:
            print(f"✓ {date}: Correctly removed")
    
    print("\n" + "="*60)
    if all_correct:
        print("✓✓✓ SUCCESS! Year B readings corrected for Easter 2027!")
    else:
        print("⚠ WARNING: Some issues remain - manual review needed")
    print("="*60)


if __name__ == '__main__':
    main()
