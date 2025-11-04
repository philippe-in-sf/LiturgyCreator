#!/usr/bin/env python3
"""
Add Holy Week feast days and Ascension Day to Year B readings
March 25-27, 2027 (Holy Week) and May 6, 2027 (Ascension)
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
    print("Adding Holy Week Feast Days and Ascension to Year B")
    print("="*60)
    
    # Load existing year_b_readings.json
    print("\n1. Loading existing year_b_readings.json...")
    with open('year_b_readings.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    year_b_data = data.get('YearB', {})
    print(f"   ✓ Loaded {len(year_b_data)} existing entries")
    
    # Define feast days to add
    feast_days = {
        '2027-03-25': {
            'name': 'Maundy Thursday',
            'url': 'https://www.lectionarypage.net/YearB_RCL/HolyWk/BMaunThu_RCL.html'
        },
        '2027-03-26': {
            'name': 'Good Friday',
            'url': 'https://www.lectionarypage.net/YearB_RCL/HolyWk/BGoodFri_RCL.html'
        },
        '2027-03-27': {
            'name': 'Holy Saturday',
            'url': 'https://www.lectionarypage.net/YearB_RCL/HolyWk/BHolySat_RCL.html'
        },
        '2027-05-06': {
            'name': 'Ascension Day',
            'url': 'https://www.lectionarypage.net/YearB_RCL/Easter/BAscension_RCL.html'
        }
    }
    
    # Fetch and add each feast day
    print("\n2. Fetching feast day readings...")
    for date, feast_info in feast_days.items():
        print(f"\n   {date}: {feast_info['name']}")
        readings = fetch_readings_from_url(feast_info['url'])
        if readings:
            year_b_data[date] = readings
            print(f"   ✓ Added {feast_info['name']}")
        else:
            print(f"   ✗ Failed to fetch {feast_info['name']}")
        time.sleep(1.5)
    
    # Save updated data
    print("\n3. Saving updated year_b_readings.json...")
    output_data = {'YearB': year_b_data}
    with open('year_b_readings.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Saved {len(year_b_data)} total entries")
    
    # Verification
    print("\n" + "="*60)
    print("VERIFICATION:")
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
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)


if __name__ == '__main__':
    main()
