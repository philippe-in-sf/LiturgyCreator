"""
Scripture Parser Module
Handles parsing and formatting of liturgical readings
"""

import logging
import re
from typing import Dict, Any, Optional

class ScriptureParser:
    """Parses and formats scripture readings for OBS display"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common scripture book abbreviations
        self.book_abbreviations = {
            'Genesis': 'Gen', 'Exodus': 'Ex', 'Leviticus': 'Lev', 'Numbers': 'Num',
            'Deuteronomy': 'Deut', 'Joshua': 'Josh', 'Judges': 'Judg', 'Ruth': 'Ruth',
            'Samuel': 'Sam', 'Kings': 'Kgs', 'Chronicles': 'Chr', 'Ezra': 'Ezra',
            'Nehemiah': 'Neh', 'Esther': 'Est', 'Job': 'Job', 'Psalms': 'Ps',
            'Proverbs': 'Prov', 'Ecclesiastes': 'Eccl', 'Song of Songs': 'Song',
            'Isaiah': 'Is', 'Jeremiah': 'Jer', 'Lamentations': 'Lam', 'Ezekiel': 'Ez',
            'Daniel': 'Dan', 'Hosea': 'Hos', 'Joel': 'Joel', 'Amos': 'Am',
            'Obadiah': 'Ob', 'Jonah': 'Jon', 'Micah': 'Mic', 'Nahum': 'Nah',
            'Habakkuk': 'Hab', 'Zephaniah': 'Zeph', 'Haggai': 'Hag', 'Zechariah': 'Zech',
            'Malachi': 'Mal', 'Matthew': 'Mt', 'Mark': 'Mk', 'Luke': 'Lk',
            'John': 'Jn', 'Acts': 'Acts', 'Romans': 'Rom', 'Corinthians': 'Cor',
            'Galatians': 'Gal', 'Ephesians': 'Eph', 'Philippians': 'Phil',
            'Colossians': 'Col', 'Thessalonians': 'Thess', 'Timothy': 'Tim',
            'Titus': 'Tit', 'Philemon': 'Phlm', 'Hebrews': 'Heb', 'James': 'Jas',
            'Peter': 'Pet', 'Jude': 'Jude', 'Revelation': 'Rev'
        }
    
    def parse_readings(self, liturgical_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Parse liturgical readings into structured format
        
        Args:
            liturgical_data: Raw liturgical data from API
            
        Returns:
            Dictionary with parsed scripture readings
        """
        if not liturgical_data or 'readings' not in liturgical_data:
            self.logger.error("No readings found in liturgical data")
            return {}
        
        parsed_readings = {}
        
        for reading_type, reading_data in liturgical_data['readings'].items():
            try:
                parsed_reading = self._parse_single_reading(reading_type, reading_data)
                if parsed_reading:
                    parsed_readings[reading_type] = parsed_reading
                    
            except Exception as e:
                self.logger.error(f"Error parsing {reading_type}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully parsed {len(parsed_readings)} readings")
        return parsed_readings
    
    def _parse_single_reading(self, reading_type: str, reading_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Parse a single scripture reading"""
        reference = reading_data.get('reference', '')
        text = reading_data.get('text', '')
        
        if not reference and not text:
            self.logger.warning(f"Empty reading data for {reading_type}")
            return None
        
        # Parse and format the reference
        formatted_reference = self._format_reference(reference)
        
        # Clean and format the text
        formatted_text = self._format_text(text)
        
        # Extract additional information
        parsed_ref = self._parse_reference(reference)
        
        return {
            'reference': formatted_reference,
            'text': formatted_text,
            'book': parsed_ref.get('book', ''),
            'chapter': parsed_ref.get('chapter', ''),
            'verses': parsed_ref.get('verses', ''),
            'full_citation': f"{parsed_ref.get('book', '')} {parsed_ref.get('chapter', '')}:{parsed_ref.get('verses', '')}"
        }
    
    def _format_reference(self, reference: str) -> str:
        """Format scripture reference for display"""
        if not reference:
            return ""
        
        # Clean up common formatting issues
        reference = reference.strip()
        reference = re.sub(r'\s+', ' ', reference)
        
        # Try to abbreviate book names
        for full_name, abbrev in self.book_abbreviations.items():
            if full_name.lower() in reference.lower():
                reference = reference.replace(full_name, abbrev)
                break
        
        return reference
    
    def _format_text(self, text: str) -> str:
        """Format scripture text for display"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove verse numbers if they exist (like [1], [2], etc.)
        text = re.sub(r'\[\d+\]\s*', '', text)
        
        # Clean up quotation marks
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Remove multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        return text
    
    def _parse_reference(self, reference: str) -> Dict[str, str]:
        """
        Parse scripture reference into components
        
        Args:
            reference: Scripture reference string (e.g., "John 3:16-17")
            
        Returns:
            Dictionary with book, chapter, and verses
        """
        if not reference:
            return {'book': '', 'chapter': '', 'verses': ''}
        
        # Common patterns for scripture references
        patterns = [
            r'^(\d*\s*[A-Za-z]+)\s+(\d+):(\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)',  # Book Chapter:Verses
            r'^(\d*\s*[A-Za-z]+)\s+(\d+):(\d+)',  # Book Chapter:Verse
            r'^(\d*\s*[A-Za-z]+)\s+(\d+)',  # Book Chapter
            r'^([A-Za-z\s]+)',  # Just book name
        ]
        
        for pattern in patterns:
            match = re.match(pattern, reference.strip())
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    return {
                        'book': groups[0].strip(),
                        'chapter': groups[1],
                        'verses': groups[2]
                    }
                elif len(groups) == 2:
                    return {
                        'book': groups[0].strip(),
                        'chapter': groups[1],
                        'verses': ''
                    }
                elif len(groups) == 1:
                    return {
                        'book': groups[0].strip(),
                        'chapter': '',
                        'verses': ''
                    }
        
        # If no pattern matches, return the whole thing as book
        return {
            'book': reference.strip(),
            'chapter': '',
            'verses': ''
        }
    
    def create_summary_text(self, parsed_readings: Dict[str, Dict[str, str]]) -> str:
        """Create a summary text of all readings"""
        if not parsed_readings:
            return "No readings available"
        
        summary_parts = []
        
        # Order readings in liturgical order
        reading_order = ['first_reading', 'psalm', 'second_reading', 'gospel']
        
        for reading_type in reading_order:
            if reading_type in parsed_readings:
                reading = parsed_readings[reading_type]
                reference = reading.get('reference', '')
                if reference:
                    if reading_type == 'psalm':
                        summary_parts.append(f"Psalm: {reference}")
                    elif reading_type == 'gospel':
                        summary_parts.append(f"Gospel: {reference}")
                    elif reading_type == 'first_reading':
                        summary_parts.append(f"First Reading: {reference}")
                    elif reading_type == 'second_reading':
                        summary_parts.append(f"Second Reading: {reference}")
        
        return " | ".join(summary_parts)
    
    def get_reading_variables(self, parsed_readings: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """
        Extract all readings as individual variables for OBS
        
        Returns:
            Flat dictionary of all scripture components
        """
        variables = {}
        
        for reading_type, reading_data in parsed_readings.items():
            prefix = reading_type.replace('_', '')
            
            for key, value in reading_data.items():
                var_name = f"{prefix}_{key}"
                variables[var_name] = value
        
        # Add summary
        variables['readings_summary'] = self.create_summary_text(parsed_readings)
        
        return variables
