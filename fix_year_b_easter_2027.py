#!/usr/bin/env python3
"""
Fix Year B Readings - Regenerate with Correct Easter 2027 Date
Corrects Easter from April 12 to March 28, 2027
Adds Holy Week feast days and Ascension Day
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Optional


class YearBReadingsFixer:
    """Fix Year B readings with correct Easter 2027 date"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.delay = 1.5
        
        # Holy Week and special feast URLs for Year B
        self.feast_days = {
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
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean up text spacing issues"""
        import re
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
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            time.sleep(self.delay)
            return response.text
        except Exception as e:
            print(f"  ERROR fetching {url}: {e}")
            return None
    
    def parse_lectionary_page(self, html: str, celebration_name: str) -> Dict:
        """Parse lectionarypage.net HTML to extract readings"""
        readings = {
            'first_reading': {'reference': '', 'text': ''},
            'psalm': {'reference': '', 'text': ''},
            'second_reading': {'reference': '', 'text': ''},
            'gospel': {'reference': '', 'text': ''},
            'collect': {'reference': '', 'text': ''}
        }
        
        try:
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
                            'text': self.clean_text(collect_p.get_text(separator=" ", strip=True))
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
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
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
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
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
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
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
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
                            }
            
        except Exception as e:
            print(f"    ERROR parsing: {e}")
        
        return readings
    
    def regenerate_readings(self):
        """Regenerate Year B readings with corrected dates"""
        
        print("="*60)
        print("FIXING YEAR B READINGS - Easter 2027: March 28 (corrected)")
        print("="*60)
        
        # Load Sunday roster (already corrected)
        print("\n1. Loading corrected Sunday roster...")
        with open('year_b_sundays.json', 'r', encoding='utf-8') as f:
            sundays = json.load(f)
        print(f"   ✓ Found {len(sundays)} Sundays")
        
        year_b_data = {}
        
        # Fetch readings for all Sundays
        print(f"\n2. Fetching readings for {len(sundays)} Sundays...")
        for idx, sunday in enumerate(sundays, 1):
            date = sunday['date']
            celebration = sunday['celebration_name']
            url = sunday['url']
            
            print(f"\n[{idx}/{len(sundays)}] {date}: {celebration}")
            
            html = self.fetch_page(url)
            if not html:
                print(f"  ⚠ Skipping - could not fetch")
                year_b_data[date] = {
                    'first_reading': {'reference': '', 'text': ''},
                    'psalm': {'reference': '', 'text': ''},
                    'second_reading': {'reference': '', 'text': ''},
                    'gospel': {'reference': '', 'text': ''},
                    'collect': {'reference': '', 'text': ''}
                }
                continue
            
            readings = self.parse_lectionary_page(html, celebration)
            year_b_data[date] = readings
            
            found_count = sum(1 for r in readings.values() if r['reference'] or r['text'])
            print(f"  ✓ Extracted {found_count}/5 readings")
        
        # Add Holy Week feast days and Ascension
        print(f"\n3. Adding Holy Week feast days and Ascension...")
        for date, feast_info in self.feast_days.items():
            print(f"\n   {date}: {feast_info['name']}")
            
            html = self.fetch_page(feast_info['url'])
            if html:
                readings = self.parse_lectionary_page(html, feast_info['name'])
                year_b_data[date] = readings
                
                found_count = sum(1 for r in readings.values() if r['reference'] or r['text'])
                print(f"  ✓ Extracted {found_count}/5 readings")
            else:
                print(f"  ⚠ Could not fetch {feast_info['name']}")
        
        # Wrap in YearB structure
        output_data = {'YearB': year_b_data}
        
        # Save to file
        print(f"\n4. Saving corrected readings to year_b_readings.json...")
        with open('year_b_readings.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✓ SUCCESS! Regenerated Year B readings")
        print(f"✓ Total dates: {len(year_b_data)}")
        print(f"✓ Sundays: {len(sundays)}")
        print(f"✓ Feast days: {len(self.feast_days)}")
        
        # Verify critical dates
        print(f"\n{'='*60}")
        print("VERIFICATION:")
        print(f"{'='*60}")
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
        
        # Check for incorrect dates that should NOT exist
        print(f"\n{'='*60}")
        print("CHECKING FOR INCORRECT DATES (should not exist):")
        print(f"{'='*60}")
        incorrect_dates = ['2027-04-08', '2027-04-09', '2027-04-10', '2027-04-12']
        for date in incorrect_dates:
            if date in year_b_data:
                print(f"✗ {date}: STILL EXISTS (should have been removed!)")
            else:
                print(f"✓ {date}: Correctly removed")
        
        print(f"\n{'='*60}")
        print("COMPLETE!")
        print(f"{'='*60}")


def main():
    fixer = YearBReadingsFixer()
    fixer.regenerate_readings()


if __name__ == '__main__':
    main()
