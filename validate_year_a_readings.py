#!/usr/bin/env python3
"""
Validation script for Year A readings JSON
Checks for spacing defects and data quality
"""

import json
import re
from typing import Dict, List, Tuple


class ReadingsValidator:
    """Validate Year A readings for spacing and quality issues"""
    
    def __init__(self, json_file: str = 'year_a_readings.json'):
        self.json_file = json_file
        self.errors = []
        self.warnings = []
        
    def load_readings(self) -> Dict:
        """Load readings from JSON file"""
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def check_spacing_defects(self, text: str, context: str) -> List[str]:
        """
        Check for spacing defects in text
        Returns list of issues found
        """
        issues = []
        
        if not text:
            return issues
        
        # Check for space before lowercase letter (potential intra-word spacing)
        # Pattern: capital letter, space, lowercase letter (e.g., "T he", "A lmighty")
        intra_word_pattern = r'\b[A-Z]\s+[a-z]'
        matches = re.finditer(intra_word_pattern, text)
        for match in matches:
            issues.append(f"Intra-word spacing: '{match.group()}' at position {match.start()}")
        
        # Check for space before punctuation
        punct_pattern = r'\s+([,.:;!?])'
        matches = re.finditer(punct_pattern, text)
        for match in matches:
            issues.append(f"Space before punctuation: ' {match.group(1)}' at position {match.start()}")
        
        # Check for possessive apostrophe with space
        possessive_pattern = r'\w+\s+\'s\b'
        matches = re.finditer(possessive_pattern, text)
        for match in matches:
            issues.append(f"Spaced possessive: '{match.group()}' at position {match.start()}")
        
        # Check for multiple consecutive spaces
        multi_space_pattern = r'\s{2,}'
        matches = re.finditer(multi_space_pattern, text)
        for match in matches:
            issues.append(f"Multiple spaces ({len(match.group())} spaces) at position {match.start()}")
        
        return issues
    
    def validate_reading(self, reading: Dict[str, str], reading_type: str, date: str) -> int:
        """
        Validate a single reading
        Returns count of errors found
        """
        error_count = 0
        
        # Check reference
        if reading.get('reference'):
            ref_issues = self.check_spacing_defects(reading['reference'], f"{date} - {reading_type} reference")
            for issue in ref_issues:
                self.errors.append(f"{date} | {reading_type} | Reference: {issue}")
                error_count += 1
        
        # Check text
        if reading.get('text'):
            text_issues = self.check_spacing_defects(reading['text'], f"{date} - {reading_type} text")
            for issue in text_issues:
                self.errors.append(f"{date} | {reading_type} | Text: {issue}")
                error_count += 1
        else:
            if reading_type != 'second_reading':  # second_reading can be empty for some dates
                self.warnings.append(f"{date} | {reading_type} has empty text")
        
        return error_count
    
    def validate_all(self) -> Tuple[int, int]:
        """
        Validate all readings
        Returns (error_count, warning_count)
        """
        print("="*70)
        print("Year A Readings Validation")
        print("="*70)
        
        data = self.load_readings()
        year_a_data = data.get('YearA', {})
        
        print(f"\nLoaded {len(year_a_data)} Sunday readings")
        
        total_errors = 0
        total_readings = 0
        
        # Validate each Sunday
        for date, readings in sorted(year_a_data.items()):
            for reading_type in ['first_reading', 'psalm', 'second_reading', 'gospel', 'collect']:
                reading = readings.get(reading_type, {})
                errors = self.validate_reading(reading, reading_type, date)
                total_errors += errors
                if reading.get('reference') or reading.get('text'):
                    total_readings += 1
        
        # Print results
        print(f"\n{'='*70}")
        print("VALIDATION RESULTS")
        print("="*70)
        print(f"Total Sundays: {len(year_a_data)}")
        print(f"Total Readings: {total_readings}")
        print(f"Errors: {total_errors}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n{'='*70}")
            print("ERRORS FOUND:")
            print("="*70)
            for error in self.errors[:50]:  # Show first 50 errors
                print(f"  ❌ {error}")
            if len(self.errors) > 50:
                print(f"  ... and {len(self.errors) - 50} more errors")
        
        if self.warnings:
            print(f"\n{'='*70}")
            print("WARNINGS:")
            print("="*70)
            for warning in self.warnings[:20]:  # Show first 20 warnings
                print(f"  ⚠️  {warning}")
            if len(self.warnings) > 20:
                print(f"  ... and {len(self.warnings) - 20} more warnings")
        
        if total_errors == 0:
            print(f"\n{'='*70}")
            print("✅ VALIDATION PASSED - No spacing defects found!")
            print("="*70)
        else:
            print(f"\n{'='*70}")
            print("❌ VALIDATION FAILED - Please fix spacing defects")
            print("="*70)
        
        return total_errors, len(self.warnings)


def main():
    """Main entry point"""
    validator = ReadingsValidator()
    error_count, warning_count = validator.validate_all()
    
    # Exit with error code if validation failed
    if error_count > 0:
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    main()
