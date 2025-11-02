#!/usr/bin/env python3
"""
Ingest Year A Episcopal RCL Readings from lectionarypage.net
Fetches and parses readings for all Sundays in Year A
"""

import json
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any


class YearAReadingsIngester:
    """Fetch and parse Year A Episcopal RCL readings from lectionarypage.net"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.delay = 1.5  # Respectful delay between requests
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Post-process text to fix spacing issues caused by BeautifulSoup's get_text(separator=" ")
        
        Fixes:
        - Intra-word spacing (e.g., "T he" → "The", "L ord" → "Lord")
        - Extra spaces (collapse multiple spaces to single space)
        - Space before punctuation (e.g., " ," → ",")
        - Possessive apostrophes (e.g., "Lord 's" → "Lord's")
        - Normalizes whitespace
        """
        if not text:
            return text
        
        # Fix intra-word spacing at start of text or after punctuation/whitespace
        # Pattern: word boundary + capital letter (except "I" and "A") + space(s) + lowercase letter(s)
        # This handles: "T he" → "The", "J esus" → "Jesus", "W hen" → "When", etc.
        # But preserves: "I will" (not "Iwill"), "A man" (not "Aman")
        text = re.sub(r'\b([B-HJ-Z])\s+([a-z])', r'\1\2', text)
        
        # Special case: "I n" → "In" (the preposition "In", not pronoun "I" + word starting with "n")
        text = re.sub(r'\b(I)\s+(n)\b', r'\1\2', text)
        
        # Also fix "A l" at start (like "A lmighty") but not "A m" (like "A man")
        # Special handling for "A" followed by specific letters that indicate split word
        text = re.sub(r'\b(A)\s+(l|g|n[d])', r'\1\2', text)
        
        # Fix possessive apostrophes: "word 's" → "word's" or "word 's" → "word's"
        # Handle both regular apostrophe (') and smart quote/right single quotation mark (')
        text = re.sub(r'\s+[\'\u2019]s\b', '\u2019s', text)
        
        # Fix space before punctuation marks
        text = re.sub(r'\s+([,.:;!?])', r'\1', text)
        
        # Fix space before closing quotes/parentheses
        text = re.sub(r'\s+(["\')\]])', r'\1', text)
        
        # Fix space after opening quotes/parentheses
        text = re.sub(r'(["\'(\[])\s+', r'\1', text)
        
        # Collapse multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
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
    
    def parse_reading_section(self, soup: BeautifulSoup, section_class: str = None, 
                             section_id: str = None) -> Dict[str, str]:
        """Parse a reading section to extract reference and text"""
        reading = {'reference': '', 'text': ''}
        
        try:
            # Try to find the section by class or id
            section = None
            if section_class:
                section = soup.find('div', class_=section_class)
            elif section_id:
                section = soup.find('div', id=section_id)
            
            if not section:
                return reading
            
            # Extract reference (usually in <strong>, <b>, or citation class)
            ref_tag = section.find(['strong', 'b', 'cite'])
            if ref_tag:
                reading['reference'] = ref_tag.get_text(separator=" ", strip=True)
            
            # Extract text (remaining paragraph content)
            paragraphs = section.find_all('p')
            text_parts = []
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                # Skip if it's just the reference
                if text and text != reading['reference']:
                    text_parts.append(text)
            
            reading['text'] = ' '.join(text_parts)
            
        except Exception as e:
            print(f"    Warning: Error parsing section: {e}")
        
        return reading
    
    def parse_lectionary_page(self, html: str, celebration_name: str) -> Dict[str, Dict[str, str]]:
        """Parse lectionarypage.net HTML to extract all readings"""
        readings = {
            'first_reading': {'reference': '', 'text': ''},
            'psalm': {'reference': '', 'text': ''},
            'second_reading': {'reference': '', 'text': ''},
            'gospel': {'reference': '', 'text': ''},
            'collect': {'reference': '', 'text': ''}
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all article sections
            articles = soup.find_all('article')
            
            for article in articles:
                # Find the h2 heading in this article
                h2 = article.find('h2', class_='lessonHeading')
                if not h2:
                    continue
                    
                heading_text = h2.get_text(separator=" ", strip=True)
                
                # Parse based on section type
                if 'Collect' in heading_text:
                    # Get the collect text from <p class="collectText">
                    collect_p = article.find('p', class_='collectText')
                    if collect_p:
                        collect_text = collect_p.get_text(separator=" ", strip=True)
                        readings['collect'] = {
                            'reference': 'The Collect',
                            'text': self.clean_text(collect_text)
                        }
                
                elif 'Old Testament' in heading_text or 'First Reading' in heading_text:
                    # Get the h3 (scripture reference)
                    h3 = article.find('h3', class_='lessonCitation')
                    if h3:
                        ref = h3.get_text(separator=" ", strip=True)
                        
                        # Get the div containing the text
                        text_div = h3.find_next_sibling('div')
                        if text_div:
                            # Get all paragraph text (lessonText and poetryText)
                            paragraphs = text_div.find_all('p', class_=['lessonText', 'poetryText'])
                            text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                            
                            readings['first_reading'] = {
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
                            }
                
                elif 'Psalm' in heading_text or 'Response' in heading_text:
                    # Get the h3 (psalm reference)
                    h3 = article.find('h3', class_='lessonCitation')
                    if h3:
                        ref = h3.get_text(separator=" ", strip=True)
                        
                        # Get the div containing the psalm text
                        text_div = h3.find_next_sibling('div')
                        if text_div:
                            # Get all psalm text paragraphs
                            paragraphs = text_div.find_all('p', class_='psalmText')
                            text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                            
                            readings['psalm'] = {
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
                            }
                
                elif 'Epistle' in heading_text or 'Second Reading' in heading_text:
                    # Get the h3 (scripture reference)
                    h3 = article.find('h3', class_='lessonCitation')
                    if h3:
                        ref = h3.get_text(separator=" ", strip=True)
                        
                        # Get the div containing the text
                        text_div = h3.find_next_sibling('div')
                        if text_div:
                            # Get all lesson text paragraphs
                            paragraphs = text_div.find_all('p', class_='lessonText')
                            text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                            
                            readings['second_reading'] = {
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
                            }
                
                elif 'Gospel' in heading_text:
                    # Get the h3 (scripture reference)
                    h3 = article.find('h3', class_='lessonCitation')
                    if h3:
                        ref = h3.get_text(separator=" ", strip=True)
                        
                        # Get the div containing the text
                        text_div = h3.find_next_sibling('div')
                        if text_div:
                            # Get all lesson text paragraphs
                            paragraphs = text_div.find_all('p', class_='lessonText')
                            text_parts = [p.get_text(separator=" ", strip=True) for p in paragraphs if p.get_text(separator=" ", strip=True)]
                            
                            readings['gospel'] = {
                                'reference': self.clean_text(ref),
                                'text': self.clean_text(' '.join(text_parts))
                            }
            
        except Exception as e:
            print(f"    ERROR parsing page for {celebration_name}: {e}")
        
        return readings
    
    def ingest_all_sundays(self, sundays_file: str = 'year_a_sundays.json',
                          output_file: str = 'year_a_readings.json') -> Dict[str, Any]:
        """Fetch and parse all Year A Sunday readings"""
        
        # Load Sunday roster
        print(f"Loading Sunday roster from {sundays_file}...")
        with open(sundays_file, 'r', encoding='utf-8') as f:
            sundays = json.load(f)
        
        print(f"Found {len(sundays)} Sundays to process")
        
        year_a_data = {}
        
        # Process each Sunday
        for idx, sunday in enumerate(sundays, 1):
            date = sunday['date']
            celebration = sunday['celebration_name']
            url = sunday['url']
            
            print(f"\n[{idx}/{len(sundays)}] {date}: {celebration}")
            
            # Fetch HTML
            html = self.fetch_page(url)
            if not html:
                print(f"  ⚠ Skipping - could not fetch page")
                year_a_data[date] = {
                    'first_reading': {'reference': '', 'text': ''},
                    'psalm': {'reference': '', 'text': ''},
                    'second_reading': {'reference': '', 'text': ''},
                    'gospel': {'reference': '', 'text': ''},
                    'collect': {'reference': '', 'text': ''}
                }
                continue
            
            # Parse readings
            readings = self.parse_lectionary_page(html, celebration)
            year_a_data[date] = readings
            
            # Show what was found
            found_count = sum(1 for r in readings.values() if r['reference'] or r['text'])
            print(f"  ✓ Extracted {found_count}/5 readings")
            
            if readings['first_reading']['reference']:
                print(f"    - First: {readings['first_reading']['reference']}")
            if readings['psalm']['reference']:
                print(f"    - Psalm: {readings['psalm']['reference']}")
            if readings['second_reading']['reference']:
                print(f"    - Second: {readings['second_reading']['reference']}")
            if readings['gospel']['reference']:
                print(f"    - Gospel: {readings['gospel']['reference']}")
            if readings['collect']['reference']:
                print(f"    - Collect: {readings['collect']['reference']}")
        
        # Wrap in YearA structure
        output_data = {
            'YearA': year_a_data
        }
        
        # Save to file
        print(f"\n{'='*60}")
        print(f"Saving to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully saved {len(year_a_data)} Sundays")
        
        # Summary
        total_readings = sum(
            1 for date_readings in year_a_data.values()
            for reading in date_readings.values()
            if reading['reference'] or reading['text']
        )
        print(f"✓ Total readings extracted: {total_readings}")
        
        return output_data


def main():
    """Main entry point"""
    print("="*60)
    print("Year A Episcopal RCL Readings Ingester")
    print("Source: lectionarypage.net")
    print("="*60)
    
    ingester = YearAReadingsIngester()
    ingester.ingest_all_sundays()
    
    print("\n" + "="*60)
    print("Ingestion complete!")
    print("="*60)


if __name__ == '__main__':
    main()
