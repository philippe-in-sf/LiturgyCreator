#!/usr/bin/env python3
"""
Ingest Year A Episcopal RCL Readings from lectionarypage.net
Fetches and parses readings for all Sundays in Year A
"""

import json
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
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
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
                reading['reference'] = ref_tag.get_text(strip=True)
            
            # Extract text (remaining paragraph content)
            paragraphs = section.find_all('p')
            text_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
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
            
            # Find all h2 headings to identify sections
            h2_headings = soup.find_all('h2')
            
            for h2 in h2_headings:
                heading_text = h2.get_text(strip=True)
                
                # Parse based on section type
                if 'Collect' in heading_text:
                    # Get the paragraph after the Collect heading
                    next_p = h2.find_next('p')
                    if next_p:
                        collect_text = next_p.get_text(strip=True)
                        readings['collect'] = {
                            'reference': 'The Collect',
                            'text': collect_text
                        }
                
                elif 'Old Testament' in heading_text or 'First Reading' in heading_text:
                    # Get the h3 (scripture reference) and text
                    h3 = h2.find_next('h3')
                    if h3:
                        ref = h3.get_text(strip=True)
                        text_parts = []
                        # Get all paragraphs until next h2 or h3
                        current = h3.find_next_sibling()
                        while current and current.name not in ['h2', 'h3']:
                            if current.name == 'p':
                                text_parts.append(current.get_text(strip=True))
                            current = current.find_next_sibling()
                        
                        readings['first_reading'] = {
                            'reference': ref,
                            'text': ' '.join(text_parts)
                        }
                
                elif 'Psalm' in heading_text:
                    # Get the h3 (psalm reference) and text
                    h3 = h2.find_next('h3')
                    if h3:
                        ref = h3.get_text(strip=True)
                        text_parts = []
                        # Get all paragraphs until next h2
                        current = h3.find_next_sibling()
                        while current and current.name != 'h2':
                            if current.name == 'p':
                                text_parts.append(current.get_text(strip=True))
                            current = current.find_next_sibling()
                        
                        readings['psalm'] = {
                            'reference': ref,
                            'text': ' '.join(text_parts)
                        }
                
                elif 'Epistle' in heading_text or 'Second Reading' in heading_text:
                    # Get the h3 (scripture reference) and text
                    h3 = h2.find_next('h3')
                    if h3:
                        ref = h3.get_text(strip=True)
                        text_parts = []
                        # Get all paragraphs until next h2
                        current = h3.find_next_sibling()
                        while current and current.name != 'h2':
                            if current.name == 'p':
                                text_parts.append(current.get_text(strip=True))
                            current = current.find_next_sibling()
                        
                        readings['second_reading'] = {
                            'reference': ref,
                            'text': ' '.join(text_parts)
                        }
                
                elif 'Gospel' in heading_text:
                    # Get the h3 (scripture reference) and text
                    h3 = h2.find_next('h3')
                    if h3:
                        ref = h3.get_text(strip=True)
                        text_parts = []
                        # Get all paragraphs until next h2
                        current = h3.find_next_sibling()
                        while current and current.name != 'h2':
                            if current.name == 'p':
                                text_parts.append(current.get_text(strip=True))
                            current = current.find_next_sibling()
                        
                        readings['gospel'] = {
                            'reference': ref,
                            'text': ' '.join(text_parts)
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
