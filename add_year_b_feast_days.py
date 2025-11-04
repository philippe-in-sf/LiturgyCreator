#!/usr/bin/env python3
"""
Add major weekday feast days to Year B readings
Matches the scope of Year A by including Christmas Eve/Day, Holy Week, and other major feasts
"""

import json
import time
import requests
from bs4 import BeautifulSoup
import re


class FeastDayAdder:
    """Add major feast days to Year B readings"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.delay = 1.5
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text by fixing spacing issues"""
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
    
    def fetch_page(self, url: str) -> str:
        """Fetch HTML from URL"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            time.sleep(self.delay)
            return response.text
        except Exception as e:
            print(f"  ERROR: {e}")
            return None
    
    def parse_lectionary_page(self, html: str) -> dict:
        """Parse readings from lectionarypage.net HTML"""
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
                
                elif 'Psalm' in heading_text:
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
    
    def add_feast_days(self):
        """Add major feast days to Year B readings"""
        
        # Load existing Year B data
        print("Loading existing Year B readings...")
        with open('year_b_readings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        year_b = data['YearB']
        
        # Define feast days to add (matching Year A scope)
        feast_days = [
            ("2026-12-24", "Christmas Eve", "https://www.lectionarypage.net/YearABC/Christmas/ChristmasEve_RCL.html"),
            ("2026-12-25", "Christmas Day", "https://www.lectionarypage.net/YearABC/Christmas/ChristmasDay_RCL.html"),
            ("2027-01-06", "The Epiphany", "https://www.lectionarypage.net/YearABC/Epiphany/Epiphany_RCL.html"),
            ("2027-02-17", "Ash Wednesday", "https://www.lectionarypage.net/YearABC/Lent/AshWed_RCL.html"),
            ("2027-04-08", "Maundy Thursday", "https://www.lectionarypage.net/YearB_RCL/HolyWk/BMaundyT_RCL.html"),
            ("2027-04-09", "Good Friday", "https://www.lectionarypage.net/YearB_RCL/HolyWk/BGoodFri_RCL.html"),
            ("2027-04-10", "Holy Saturday", "https://www.lectionarypage.net/YearABC/HolyWk/HolySat_RCL.html"),
            ("2027-05-21", "Ascension Day", "https://www.lectionarypage.net/YearB_RCL/Easter/BAscension_RCL.html"),
        ]
        
        print(f"\nAdding {len(feast_days)} major feast days...\n")
        
        added_count = 0
        for date, name, url in feast_days:
            print(f"[{added_count + 1}/{len(feast_days)}] {date}: {name}")
            
            # Check if already exists
            if date in year_b:
                print(f"  ✓ Already exists, skipping")
                continue
            
            # Fetch readings
            html = self.fetch_page(url)
            if not html:
                print(f"  ⚠ Could not fetch, adding empty entry")
                year_b[date] = {
                    'first_reading': {'reference': '', 'text': ''},
                    'psalm': {'reference': '', 'text': ''},
                    'second_reading': {'reference': '', 'text': ''},
                    'gospel': {'reference': '', 'text': ''},
                    'collect': {'reference': '', 'text': ''}
                }
                continue
            
            # Parse readings
            readings = self.parse_lectionary_page(html)
            year_b[date] = readings
            
            found_count = sum(1 for r in readings.values() if r['reference'] or r['text'])
            print(f"  ✓ Added with {found_count}/5 readings")
            
            if readings['gospel']['reference']:
                print(f"    Gospel: {readings['gospel']['reference']}")
            
            added_count += 1
        
        # Save updated data
        print(f"\n{'='*60}")
        print("Saving updated Year B readings...")
        
        with open('year_b_readings.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully updated Year B readings")
        print(f"✓ Total entries: {len(year_b)}")
        print(f"✓ Added {added_count} new feast days")


def main():
    """Main entry point"""
    print("="*60)
    print("Adding Major Feast Days to Year B")
    print("="*60)
    
    adder = FeastDayAdder()
    adder.add_feast_days()
    
    print("\n" + "="*60)
    print("Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
