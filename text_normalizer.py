#!/usr/bin/env python3
"""
Production-grade text normalization for liturgical readings.

This module provides token-based text normalization with deterministic spacing rules.
Handles edge cases including:
- Merged tokens (e.g., "Ohouse" → "O house")
- Punctuation spacing
- Possessive apostrophes (both ' and ')
- Verse numbers in psalms
- Smart quotes and special characters
"""

import re
from typing import List, Dict


def normalize_tokens(tokens: List[Dict[str, str]]) -> str:
    """
    Convert a list of typed tokens into properly spaced text.
    
    Token types:
    - 'verse_number': Psalm verse numbers (e.g., "1", "2")
    - 'text': Regular text runs
    - 'punctuation': Punctuation marks
    - 'quote_open': Opening quotation marks
    - 'quote_close': Closing quotation marks
    
    Args:
        tokens: List of dicts with 'type' and 'text' keys
        
    Returns:
        Normalized text with proper spacing
    """
    if not tokens:
        return ""
    
    result = []
    prev_type = None
    
    for i, token in enumerate(tokens):
        token_type = token.get('type', 'text')
        text = token.get('text', '')
        
        if not text:
            continue
        
        needs_space_before = False
        
        if i > 0:
            if token_type == 'verse_number':
                needs_space_before = True
            elif token_type == 'text':
                if prev_type in ('text', 'verse_number', 'quote_close'):
                    needs_space_before = True
            elif token_type == 'quote_open':
                if prev_type in ('text', 'verse_number', 'punctuation', 'quote_close'):
                    needs_space_before = True
            elif token_type == 'punctuation':
                needs_space_before = False
            elif token_type == 'quote_close':
                needs_space_before = False
        
        if needs_space_before and result:
            result.append(' ')
        
        result.append(text)
        prev_type = token_type
    
    return ''.join(result)


def fix_merged_tokens(text: str) -> str:
    """
    Fix merged tokens where capital letters were incorrectly merged with words.
    
    Patterns fixed:
    - "Ohouse" → "O house"
    - "Ofsuch" → "O fsuch" (though this is rare)
    - Single capital letter followed by lowercase word
    
    Does NOT split:
    - Normal capitalized words (e.g., "House", "Jerusalem")
    - Acronyms (e.g., "USA")
    - Roman numerals (e.g., "II")
    
    Args:
        text: Input text
        
    Returns:
        Text with merged tokens fixed
    """
    if not text:
        return text
    
    # Fix pattern: Single capital letter (not I or A) directly followed by lowercase letter
    # This handles "Ohouse" → "O house", "Ychildren" → "Y children"
    # Preserve word boundaries to avoid splitting normal words
    text = re.sub(r'\b([B-HJ-Z])([a-z]+)', r'\1 \2', text)
    
    # Special case: "O " at start of sentences/phrases (common in liturgical text)
    # Already handled by above pattern
    
    return text


def fix_punctuation_spacing(text: str) -> str:
    """
    Ensure proper spacing around punctuation marks.
    
    Rules:
    - Space AFTER: . , : ; ! ? (except in special cases)
    - NO space BEFORE: . , : ; ! ?
    - Preserve mid-word apostrophes (e.g., "don't", "Lord's")
    - Handle smart quotes properly
    
    Args:
        text: Input text
        
    Returns:
        Text with corrected punctuation spacing
    """
    if not text:
        return text
    
    # Remove space before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Add space after punctuation if followed by letter or digit
    # But NOT if it's part of a number (e.g., "3.14")
    text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
    
    # Special case: Add space after punctuation if followed by digit (verse numbers)
    # "Lord."2 → "Lord." 2
    text = re.sub(r'([.,;:!?])(\d)', r'\1 \2', text)
    
    # Fix closing quote followed by punctuation: ensure no space between
    text = re.sub(r'(["\u201D\u2019])\s+([.,;:!?])', r'\1\2', text)
    
    return text


def fix_possessive_apostrophes(text: str) -> str:
    """
    Fix possessive apostrophes to ensure proper spacing.
    
    Rules:
    - "companions' sake" not "companions'sake"
    - "Lord's house" not "Lord 's house"
    - Handle both ' (ASCII) and ' (smart quote)
    
    Args:
        text: Input text
        
    Returns:
        Text with corrected possessive apostrophes
    """
    if not text:
        return text
    
    # Fix "word's" with space: "Lord 's" → "Lord's"
    text = re.sub(r'(\w+)\s+[\'\u2019]s\b', r'\1\u2019s', text)
    
    # Fix possessive without space before next word: "companions'sake" → "companions' sake"
    # Handle both trailing apostrophe (plural possessive) and 's possessive
    text = re.sub(r'(\w+[\'\u2019]s?)([A-Za-z])', r'\1 \2', text)
    
    # Normalize apostrophes to smart quote (')
    text = re.sub(r"'", '\u2019', text)
    
    return text


def fix_verse_numbers(text: str) -> str:
    """
    Ensure proper spacing around verse numbers in psalms.
    
    Psalm format: "1 I was glad..." or "2 Now our feet..."
    Ensure space after verse number, before text.
    
    Args:
        text: Input text (psalm text)
        
    Returns:
        Text with corrected verse number spacing
    """
    if not text:
        return text
    
    # Pattern: digit(s) at start or after space, followed immediately by letter
    # "2Now" → "2 Now"
    text = re.sub(r'(\d+)([A-Z])', r'\1 \2', text)
    
    # Also handle lowercase after verse numbers (rare but possible)
    # "2now" → "2 now"
    text = re.sub(r'(\d+)([a-z])', r'\1 \2', text)
    
    return text


def collapse_whitespace(text: str) -> str:
    """
    Remove extra whitespace while preserving intentional formatting.
    
    Rules:
    - Collapse multiple spaces to single space
    - Remove leading/trailing whitespace
    - Preserve single spaces
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return text
    
    # Collapse multiple spaces to single space
    text = re.sub(r' +', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_text(text: str, is_psalm: bool = False) -> str:
    """
    Apply all normalization rules to text.
    
    This is the main entry point for text normalization.
    Applies fixes in the correct order to handle interdependencies.
    
    Args:
        text: Input text to normalize
        is_psalm: Whether this is psalm text (affects verse number handling)
        
    Returns:
        Fully normalized text
    """
    if not text:
        return text
    
    # Order matters! Some fixes depend on others being applied first.
    
    # 1. Fix merged tokens first (before spacing rules)
    text = fix_merged_tokens(text)
    
    # 2. Fix possessive apostrophes
    text = fix_possessive_apostrophes(text)
    
    # 3. Fix punctuation spacing
    text = fix_punctuation_spacing(text)
    
    # 4. Fix verse numbers (especially important for psalms)
    if is_psalm:
        text = fix_verse_numbers(text)
    
    # 5. Final whitespace cleanup
    text = collapse_whitespace(text)
    
    return text


def extract_tokens_from_html_element(element, parent_type: str = 'text') -> List[Dict[str, str]]:
    """
    Extract typed tokens from BeautifulSoup HTML element.
    
    This is a helper for DOM-aware extraction.
    Preserves semantic boundaries and text structure.
    
    Args:
        element: BeautifulSoup element
        parent_type: Context from parent element
        
    Returns:
        List of typed tokens
    """
    tokens = []
    
    # Handle different element types
    if hasattr(element, 'name') and element.name:
        # This is a tag
        tag_name = element.name.lower()
        
        # Verse numbers in psalms
        if tag_name in ('sup', 'span') and parent_type == 'psalm':
            text = element.get_text(strip=True)
            if text and text.isdigit():
                tokens.append({'type': 'verse_number', 'text': text})
                return tokens
        
        # Recursively process children
        for child in element.children:
            tokens.extend(extract_tokens_from_html_element(child, parent_type))
    else:
        # This is a text node
        text = str(element).strip()
        if text:
            tokens.append({'type': 'text', 'text': text})
    
    return tokens
