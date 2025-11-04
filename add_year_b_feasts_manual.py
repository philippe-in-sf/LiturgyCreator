#!/usr/bin/env python3
"""
Manually add major feast days to Year B readings with corrected URLs
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
        })
        self.delay = 1.5
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text"""
        if not text:
            return text
        text = re.sub(r'\b([B-HJ-Z])\s+([a-z])', r'\1\2', text)
        text = re.sub(r'\b(I)\s+(n)\b', r'\1\2', text)
        text = re.sub(r'\b(A)\s+(l|g|n[d])', r'\1\2', text)
        text = re.sub(r'\s+[\'\u2019]s\b', '\u2019s', text)
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def fetch_and_parse(self, url: str) -> dict:
        """Fetch and parse readings from URL"""
        try:
            print(f"  Trying: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(self.delay)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            readings = {
                'first_reading': {'reference': '', 'text': ''},
                'psalm': {'reference': '', 'text': ''},
                'second_reading': {'reference': '', 'text': ''},
                'gospel': {'reference': '', 'text': ''},
                'collect': {'reference': '', 'text': ''}
            }
            
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
            
            return readings
        except Exception as e:
            print(f"  ERROR: {e}")
            return None
    
    def add_feast_days(self):
        """Add feast days with corrected URLs"""
        
        # Load existing data
        with open('year_b_readings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        year_b = data['YearB']
        
        # Feast days with multiple URL attempts
        feast_days = [
            ("2026-12-24", "Christmas Eve", [
                "https://www.lectionarypage.net/YearABC/Christmas/XmasEve.html",
                "https://www.lectionarypage.net/YearABC/Christmas/ChristmasEve.html"
            ]),
            ("2026-12-25", "Christmas Day", [
                "https://www.lectionarypage.net/YearABC/Christmas/XmasDay.html",
                "https://www.lectionarypage.net/YearABC/Christmas/ChristmasDay.html"
            ]),
            ("2027-01-06", "The Epiphany", [
                "https://www.lectionarypage.net/YearABC/Epiphany/Epiphany.html",
                "https://www.lectionarypage.net/YearABC/HolyDays/Epiphany.html"
            ]),
            ("2027-02-17", "Ash Wednesday", [
                "https://www.lectionarypage.net/YearABC/Lent/AshWed.html",
                "https://www.lectionarypage.net/YearABC/Lent/AshWednesday.html"
            ]),
            ("2027-04-08", "Maundy Thursday", [
                "https://www.lectionarypage.net/YearB_RCL/HolyWk/BMaundyTh.html",
                "https://www.lectionarypage.net/YearABC/HolyWk/MaundyTh.html"
            ]),
            ("2027-04-09", "Good Friday", [
                "https://www.lectionarypage.net/YearB_RCL/HolyWk/BGoodFri.html",
                "https://www.lectionarypage.net/YearABC/HolyWk/GoodFri.html"
            ]),
            ("2027-04-10", "Holy Saturday", [
                "https://www.lectionarypage.net/YearB_RCL/HolyWk/BHolySat.html",
                "https://www.lectionarypage.net/YearABC/HolyWk/HolySat.html"
            ]),
        ]
        
        print(f"\nAdding {len(feast_days)} feast days...\n")
        
        added = 0
        for date, name, urls in feast_days:
            if date in year_b and year_b[date].get('gospel', {}).get('reference'):
                print(f"{date}: {name} - Already complete")
                continue
            
            print(f"{date}: {name}")
            
            # Try each URL
            readings = None
            for url in urls:
                readings = self.fetch_and_parse(url)
                if readings and readings['gospel']['reference']:
                    break
            
            if readings:
                year_b[date] = readings
                found = sum(1 for r in readings.values() if r['reference'] or r['text'])
                print(f"  ✓ Added with {found}/5 readings")
                added += 1
            else:
                print(f"  ⚠ Could not fetch")
        
        # Save
        with open('year_b_readings.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Added {added} feast days")
        print(f"✓ Total entries: {len(year_b)}")


if __name__ == '__main__':
    adder = FeastDayAdder()
    adder.add_feast_days()
