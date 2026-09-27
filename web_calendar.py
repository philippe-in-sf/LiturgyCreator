#!/usr/bin/env python3
"""
Web-based Interactive Liturgical Calendar
Episcopal Church Calendar with Revised Common Lectionary integration
Version: 1.9 - OBS Scene Generation
"""

from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, session, redirect, url_for
import calendar
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import zipfile
import io
import textwrap
import re
import requests
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import uuid
import base64
from liturgy_fetcher import LiturgyFetcher
from scripture_parser import ScriptureParser

app = Flask(__name__)

# Configure secret key for sessions
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_branding_config() -> Dict[str, Any]:
    """Load branding configuration from JSON file, returns defaults if file missing/corrupt"""
    config_path = 'config/branding_config.json'
    default_config = {
        "church_name": "Trinity Episcopal Church",
        "logo_path": None,
        "custom_colors": {
            "enabled": False,
            "primary": "#4169E1",
            "accent": "#FFD700",
            "background": "#FFFFFF"
        },
        "custom_font": {
            "enabled": False,
            "family": "Arial"
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config
        else:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    except Exception as e:
        print(f"Error loading branding config: {e}")
        return default_config

def save_branding_config(config: Dict[str, Any]) -> bool:
    """Save branding configuration to JSON file with validation"""
    config_path = 'config/branding_config.json'
    
    try:
        if 'church_name' in config:
            if len(config['church_name']) > 100:
                raise ValueError("Church name must be 100 characters or less")
        
        if 'custom_colors' in config and config['custom_colors'].get('enabled'):
            color_pattern = r'^#[0-9A-Fa-f]{6}$'
            colors = config['custom_colors']
            if 'primary' in colors and not re.match(color_pattern, colors['primary']):
                raise ValueError("Invalid primary color format")
            if 'accent' in colors and not re.match(color_pattern, colors['accent']):
                raise ValueError("Invalid accent color format")
            if 'background' in colors and not re.match(color_pattern, colors['background']):
                raise ValueError("Invalid background color format")
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving branding config: {e}")
        raise

def get_branding_logo_path() -> Optional[str]:
    """Returns absolute path to logo if exists, None otherwise"""
    config = load_branding_config()
    logo_path = config.get('logo_path')
    
    if logo_path and os.path.exists(logo_path):
        return os.path.abspath(logo_path)
    return None

def load_stack_sans_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Load Stack Sans font from local fonts directory with fallback to DejaVu
    
    Args:
        size: Font size in points
        bold: If True, use Headline variant (for emphasis), otherwise Text variant
    
    Returns:
        ImageFont object (either Stack Sans or fallback)
    """
    # Try Stack Sans from local fonts directory first
    # Stack Sans Text is for body text, Headline is for titles/headings
    try:
        font_path = "fonts/StackSans-Headline.ttf" if bold else "fonts/StackSans-Text.ttf"
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"⚠️ Could not load Stack Sans font: {e}")
    
    # Fallback to DejaVu fonts
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        else:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        print(f"⚠️ Could not load DejaVu font, using default")
        return ImageFont.load_default()

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract text from PDF using pdfplumber and fallback to OCR if needed"""
    try:
        extracted_text = ""
        page_count = 0
        
        # Try text extraction with pdfplumber first
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n"
        
        # If no text extracted, try OCR as fallback
        if not extracted_text.strip():
            try:
                # Convert PDF to images and use OCR
                try:
                    import fitz  # PyMuPDF for PDF to image conversion
                except ImportError:
                    return {
                        'success': True,
                        'text': extracted_text.strip(),
                        'page_count': page_count,
                        'method': 'pdfplumber'
                    }
                
                doc = fitz.open(pdf_path)
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Use PIL to open the image
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Use tesseract for OCR
                    page_text = pytesseract.image_to_string(img)
                    if page_text:
                        extracted_text += page_text + "\n\n"
                
                doc.close()
                
            except ImportError:
                # PyMuPDF not available, skip OCR fallback
                pass
        
        return {
            'success': True,
            'text': extracted_text.strip(),
            'page_count': page_count,
            'method': 'pdfplumber' if extracted_text else 'ocr'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'text': '',
            'page_count': 0
        }

def process_liturgical_pdf(text: str) -> Dict[str, Any]:
    """Process extracted PDF text to identify liturgical content"""
    try:
        # Common liturgical section identifiers
        section_patterns = {
            'first_reading': r'(?i)(?:first\s+reading|lesson\s+1|old\s+testament)',
            'psalm': r'(?i)(?:psalm|responsorial)',
            'second_reading': r'(?i)(?:second\s+reading|lesson\s+2|epistle|new\s+testament)',
            'gospel': r'(?i)(?:gospel|holy\s+gospel)',
            'hymns': r'(?i)(?:hymn|song|anthem)',
            'prayers': r'(?i)(?:prayer|collect|intercession)',
            'service_info': r'(?i)(?:service|worship|celebration|date|time)'
        }
        
        # Split text into sections
        sections = {}
        lines = text.split('\n')
        current_section = 'general'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line matches any section pattern
            section_found = False
            for section_key, pattern in section_patterns.items():
                if re.search(pattern, line):
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = section_key
                    current_content = [line]
                    section_found = True
                    break
            
            if not section_found:
                current_content.append(line)
        
        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return {
            'success': True,
            'sections': sections,
            'full_text': text
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'sections': {},
            'full_text': text
        }

def format_text_with_paragraphs(text: str, width: int = 50) -> str:
    """
    Format text with word wrapping while preserving paragraph structure.
    Handles scripture passages by maintaining natural breaks.
    """
    if not text:
        return text
    
    # Split text into sentences that likely represent paragraph breaks
    # Look for periods followed by space and capital letter, or double quotes with period
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"])|(?<=[.!?]")\s+(?=[A-Z])', text.strip())
    
    formatted_paragraphs = []
    current_paragraph = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if this sentence should start a new paragraph
        # Common indicators: starts with certain words or follows a quote
        new_paragraph_indicators = [
            'But ', 'And ', 'For ', 'Then ', 'Now ', 'When ', 'So ', 'Therefore ',
            'He said', 'She said', 'Jesus said', 'The Lord', 'Thus says'
        ]
        
        start_new_paragraph = (
            len(current_paragraph) >= 3 or  # Prevent overly long paragraphs
            (current_paragraph and any(sentence.startswith(indicator) for indicator in new_paragraph_indicators))
        )
        
        if start_new_paragraph and current_paragraph:
            # Join current paragraph and wrap it
            paragraph_text = ' '.join(current_paragraph)
            wrapped_paragraph = textwrap.fill(paragraph_text, width=width, break_long_words=False, break_on_hyphens=False)
            formatted_paragraphs.append(wrapped_paragraph)
            current_paragraph = [sentence]
        else:
            current_paragraph.append(sentence)
    
    # Handle remaining sentences
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph)
        wrapped_paragraph = textwrap.fill(paragraph_text, width=width, break_long_words=False, break_on_hyphens=False)
        formatted_paragraphs.append(wrapped_paragraph)
    
    # Join paragraphs with double line breaks for clear separation
    return '\n\n'.join(formatted_paragraphs)

def search_hymn_by_title(title: str) -> dict:
    """
    Search for a hymn by title using Hymnary.org's search functionality.
    Returns hymn metadata including text link.
    """
    try:
        # Clean up the title for searching - remove hymn numbers and extra info
        clean_title = re.sub(r'^(Hymn\s+\d+\s*[-:]?\s*)', '', title, flags=re.IGNORECASE)
        clean_title = re.sub(r'\s*[-:]\s*.+$', '', clean_title)  # Remove subtitle after dash/colon
        clean_title = clean_title.strip()
        
        # Use Hymnary's search API by trying scripture references first, then fallback to direct search
        # For now, we'll construct a search URL and try to parse results
        search_url = f"https://hymnary.org/search"
        params = {
            'qu': f'title:"{clean_title}"',
            'export': 'csv'
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            # Parse CSV response to find hymn
            lines = response.text.strip().split('\n')
            if len(lines) > 1:  # Has header + data
                # Simple CSV parsing - look for title match in first data row
                data_line = lines[1] if len(lines) > 1 else ""
                if clean_title.lower() in data_line.lower():
                    # Extract the text link from the CSV data
                    # This is a simplified approach - in production might need more robust CSV parsing
                    return {
                        'title': clean_title,
                        'found': True,
                        'search_term': clean_title
                    }
        
        return {
            'title': title,
            'found': False,
            'search_term': clean_title
        }
        
    except Exception as e:
        print(f"Error searching for hymn '{title}': {e}")
        return {
            'title': title,
            'found': False,
            'error': str(e)
        }

def fetch_hymn_text_from_hymnary(hymn_title: str) -> str:
    """
    Attempt to fetch hymn text from Hymnary.org.
    Note: Due to copyright restrictions, this returns a placeholder message.
    """
    try:
        hymn_info = search_hymn_by_title(hymn_title)
        
        if hymn_info.get('found'):
            # For copyright reasons, we can't reproduce full hymn texts
            # Instead, provide a helpful reference
            return f"Hymn: {hymn_info['title']}\n\nFor the complete text of this hymn, please visit:\nhttps://hymnary.org\n\nSearch for: {hymn_info['search_term']}\n\nNote: Hymn texts are protected by copyright and cannot be\nautomatically included in this export. Please obtain proper\nlicensing for use in worship services."
        else:
            return f"Hymn: {hymn_title}\n\nThis hymn was not found in the Hymnary.org database.\nPlease verify the title and search manually at:\nhttps://hymnary.org\n\nNote: Hymn texts are protected by copyright. Please obtain\nproper licensing for use in worship services."
            
    except Exception as e:
        return f"Hymn: {hymn_title}\n\nUnable to search Hymnary.org database.\nError: {str(e)}\n\nPlease search manually at: https://hymnary.org\n\nNote: Hymn texts are protected by copyright. Please obtain\nproper licensing for use in worship services."

class WebLiturgicalCalendar:
    """Web-based liturgical calendar"""
    
    def __init__(self):
        self.liturgy_fetcher = LiturgyFetcher()
        self.scripture_parser = ScriptureParser()
        
        # Liturgical colors
        self.liturgical_colors = {
            'advent': '#4169E1',      # Royal Blue (Episcopal tradition)
            'gaudete': '#FF69B4',     # Pink/Rose for Gaudete Sunday (3rd Sunday of Advent)
            'christmas': '#D4AF37',   # Gold
            'epiphany': '#00AA00',   # Green
            'lent': '#663399',       # Purple
            'palm_sunday': '#AA0000', # Red
            'maundy_thursday': '#FFFFFF', # White
            'good_friday': '#000000', # Black
            'easter': '#FFFFFF',     # White
            'pentecost': '#AA0000',  # Red
            'ordinary': '#00AA00',   # Green (Season after Pentecost)
            'feast': '#FFFFFF',      # White for major feasts
            'martyr': '#AA0000',     # Red for martyrs
            'default': '#F0F0F0'     # Light gray
        }
        
        # Cache for readings
        self.readings_cache = {}
        
    def get_liturgical_year(self, date_obj: datetime) -> str:
        """Determine the liturgical year (A, B, or C)"""
        if date_obj.year == 2025:
            # First Sunday of Advent 2025 is Nov 30 - this begins Year A
            if (date_obj.month == 11 and date_obj.day >= 30) or date_obj.month == 12:
                return "Year A"
            else:
                return "Year C"
        elif date_obj.year == 2024:
            return "Year C"
        elif date_obj.year == 2026:
            return "Year A"
        else:
            cycle_year = (date_obj.year - 2022) % 3
            return ['Year A', 'Year B', 'Year C'][cycle_year]
            
    def calculate_easter(self, year: int) -> date:
        """Calculate Easter Sunday for a given year using Computus algorithm (Western/Gregorian)"""
        # Anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        
        return date(year, month, day)
    
    def get_movable_feast_day(self, date_obj: date) -> Optional[tuple]:
        """Check if date is a movable feast day (based on Easter or Epiphany)
        Returns tuple of (feast_name, color_override) or None"""
        
        year = date_obj.year
        easter_date = self.calculate_easter(year)
        
        # Calculate movable feast days based on Easter
        ash_wednesday = easter_date - timedelta(days=46)
        palm_sunday = easter_date - timedelta(days=7)
        maundy_thursday = easter_date - timedelta(days=3)
        good_friday = easter_date - timedelta(days=2)
        holy_saturday = easter_date - timedelta(days=1)
        ascension = easter_date + timedelta(days=39)  # 40 days after Easter
        pentecost = easter_date + timedelta(days=49)  # 50 days after Easter
        trinity_sunday = easter_date + timedelta(days=56)  # Week after Pentecost
        
        # Calculate Baptism of Our Lord (First Sunday after Epiphany)
        epiphany = date(year, 1, 6)
        days_until_sunday = (6 - epiphany.weekday()) % 7  # Days until next Sunday
        if days_until_sunday == 0:
            days_until_sunday = 7  # If Epiphany is Sunday, Baptism is next Sunday
        baptism_of_our_lord = epiphany + timedelta(days=days_until_sunday)
        
        # Check for movable feasts with their liturgical colors
        movable_feasts = {
            baptism_of_our_lord: ("The Baptism of Our Lord", "epiphany"),
            ash_wednesday: ("Ash Wednesday", "lent"),
            palm_sunday: ("Palm Sunday", "palm_sunday"),
            maundy_thursday: ("Maundy Thursday", "maundy_thursday"),
            good_friday: ("Good Friday", "good_friday"),
            holy_saturday: ("Holy Saturday", "lent"),
            easter_date: ("Easter Sunday", "easter"),
            ascension: ("Ascension Day", "easter"),
            pentecost: ("Pentecost", "pentecost"),
            trinity_sunday: ("Trinity Sunday", "feast")
        }
        
        if date_obj in movable_feasts:
            return movable_feasts[date_obj]
        
        return None
            
    def get_liturgical_season(self, date_obj: datetime) -> str:
        """Determine the current liturgical season"""
        # Convert to date if datetime
        if isinstance(date_obj, datetime):
            check_date = date_obj.date()
        else:
            check_date = date_obj
        
        year = check_date.year
        month = check_date.month
        day = check_date.day
        
        # Calculate Easter for this year
        easter_date = self.calculate_easter(year)
        
        # Calculate key liturgical dates
        ash_wednesday = easter_date - timedelta(days=46)
        holy_saturday = easter_date - timedelta(days=1)
        pentecost = easter_date + timedelta(days=49)
        
        # Christmas Season: Dec 25 - Jan 6
        if (month == 12 and day >= 25) or (month == 1 and day <= 6):
            return "Christmas Season"
        
        # Season after Epiphany: Jan 7 until Ash Wednesday
        if month == 1 and day > 6:
            return "Season after Epiphany"
        
        # Check if we're before Ash Wednesday (still Epiphany season)
        if check_date < ash_wednesday:
            return "Season after Epiphany"
        
        # Lent: Ash Wednesday through Holy Saturday
        if ash_wednesday <= check_date <= holy_saturday:
            return "Lenten Season"
        
        # Easter Season: Easter Sunday through Pentecost (50 days)
        if easter_date <= check_date <= pentecost:
            return "Easter Season"
        
        # Advent: 4 Sundays before Christmas
        christmas = date(year, 12, 25)
        days_until_sunday = (christmas.weekday() + 1) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        fourth_sunday_before = christmas - timedelta(days=(3 * 7 + days_until_sunday))
        
        if check_date >= fourth_sunday_before and month == 11:
            return "Advent Season"
        if month == 12 and day < 25:
            return "Advent Season"
        
        # Everything else is Season after Pentecost (Ordinary Time)
        return "Season after Pentecost"
            
    def get_liturgical_info(self, date_obj: date) -> Dict:
        """Get liturgical information for a specific date"""
        weekday = date_obj.weekday()
        is_sunday = (weekday == 6)
        
        season = self.get_liturgical_season(datetime.combine(date_obj, datetime.min.time()))
        
        color_map = {
            'Advent Season': 'advent',
            'Christmas Season': 'christmas',
            'Season after Epiphany': 'epiphany',
            'Lenten Season': 'lent',
            'Easter Season': 'easter',
            'Season after Pentecost': 'ordinary'
        }
        
        color = color_map.get(season, 'default')
        
        # Check for movable feast days first (these override seasonal colors)
        movable_feast = self.get_movable_feast_day(date_obj)
        if movable_feast:
            feast_day = movable_feast[0]
            color = movable_feast[1]
        else:
            # Check for Gaudete Sunday (3rd Sunday of Advent - pink)
            if self.is_gaudete_sunday(date_obj):
                feast_day = "Gaudete Sunday (Third Sunday of Advent)"
                color = 'gaudete'
            else:
                # Check for fixed feast days
                feast_day = self.get_feast_day(date_obj)
                if feast_day:
                    color = 'feast'
            
        return {
            'is_sunday': is_sunday,
            'color': color,
            'season': season,
            'feast_day': feast_day,
            'hex_color': self.liturgical_colors.get(color, self.liturgical_colors['default'])
        }
        
    def get_feast_day(self, date_obj: date) -> Optional[str]:
        """Check if date is a special feast day"""
        month = date_obj.month
        day = date_obj.day
        
        # Dictionary mapping (month, day) tuples to feast day names
        # Note: Movable feasts (Maundy Thursday, Good Friday, Holy Saturday, Easter, Pentecost, etc.)
        # are handled by get_movable_feast_day() and should not be listed here
        feast_days = {
            (1, 1): "The Holy Name of Our Lord Jesus Christ",
            (1, 6): "The Epiphany of Our Lord",
            (7, 4): "Independence Day",
            (8, 15): "St Mary, the Virgin",
            (9, 29): "St Michael and All Angels",
            (11, 1): "All Saints' Day",
            (11, 2): "All Souls' Day",
            (12, 24): "The Nativity of Our Lord: Christmas Eve",
            (12, 25): "The Nativity of Our Lord: Christmas Day",
            (12, 26): "St Stephen, Deacon and Martyr"
        }
        
        # Use explicit key lookup to avoid type issues
        key = (month, day)
        if key in feast_days:
            return feast_days[key]
        return None
        
    def is_gaudete_sunday(self, date_obj: date) -> bool:
        """Check if the given date is Gaudete Sunday (3rd Sunday of Advent)"""
        # First, check if we're in Advent season
        if date_obj.month not in [11, 12]:
            return False
        
        # Check if it's a Sunday
        if date_obj.weekday() != 6:  # 6 = Sunday
            return False
        
        # Find Christmas Day of this year
        year = date_obj.year
        christmas = date(year, 12, 25)
        
        # Find the 4th Sunday before Christmas (First Sunday of Advent)
        # Christmas can fall on any day, so we need to count backwards
        days_until_sunday = (christmas.weekday() + 1) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        
        # Fourth Sunday before Christmas
        fourth_sunday_before = christmas - timedelta(days=(3 * 7 + days_until_sunday))
        first_advent = fourth_sunday_before
        
        # Third Sunday of Advent (Gaudete) is 2 weeks after First Advent
        gaudete_sunday = first_advent + timedelta(days=14)
        
        return date_obj == gaudete_sunday
        
    def get_sunday_name(self, date_obj: datetime) -> str:
        """Get the proper name for Sunday in the liturgical calendar"""
        season = self.get_liturgical_season(date_obj)
        
        # Convert datetime to date if needed
        if isinstance(date_obj, datetime):
            check_date = date_obj.date()
        else:
            check_date = date_obj
        
        year = check_date.year
        
        # Epiphany season - calculate which Sunday after Epiphany
        if season == "Season after Epiphany":
            epiphany = date(year, 1, 6)
            # Find first Sunday after Epiphany (Baptism of Our Lord)
            days_until_sunday = (6 - epiphany.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            first_sunday_after = epiphany + timedelta(days=days_until_sunday)
            
            # Count weeks since Baptism of Our Lord (which is First Sunday after Epiphany)
            days_diff = (check_date - first_sunday_after).days
            week_num = (days_diff // 7) + 1  # Baptism is 1st, so +7 days is 2nd, etc.
            
            ordinals = ['', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth']
            if week_num < len(ordinals):
                return f"{ordinals[week_num]} Sunday after the Epiphany"
            else:
                return f"{week_num}th Sunday after the Epiphany"
        
        # Pentecost season
        if "Pentecost" in season:
            week_of_year = date_obj.isocalendar()[1]
            if week_of_year >= 20 and week_of_year <= 45:
                proper_num = week_of_year - 19
                return f"Proper {proper_num} (Sunday after Pentecost)"
        
        # Advent season
        if season == "Advent":
            christmas = date(year, 12, 25)
            days_until_sunday = (christmas.weekday() + 1) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            fourth_sunday_before = christmas - timedelta(days=(3 * 7 + days_until_sunday))
            first_advent = fourth_sunday_before
            
            days_diff = (check_date - first_advent).days
            week_num = (days_diff // 7) + 1
            
            ordinals = ['', 'First', 'Second', 'Third', 'Fourth']
            if week_num <= 4:
                return f"{ordinals[week_num]} Sunday of Advent"
        
        # Lent season
        if season == "Lent":
            easter = self._calculate_easter(year)
            ash_wednesday = easter - timedelta(days=46)
            first_sunday_lent = ash_wednesday + timedelta(days=(6 - ash_wednesday.weekday() + 7) % 7 + 1)
            if first_sunday_lent < ash_wednesday:
                first_sunday_lent += timedelta(days=7)
            # Find first Sunday of Lent (Sunday after Ash Wednesday)
            days_after_ash = (6 - ash_wednesday.weekday()) % 7
            if days_after_ash == 0:
                days_after_ash = 7
            first_sunday_lent = ash_wednesday + timedelta(days=days_after_ash)
            
            days_diff = (check_date - first_sunday_lent).days
            week_num = (days_diff // 7) + 1
            
            ordinals = ['', 'First', 'Second', 'Third', 'Fourth', 'Fifth']
            if week_num <= 5:
                return f"{ordinals[week_num]} Sunday in Lent"
        
        # Easter season
        if season == "Easter":
            easter = self._calculate_easter(year)
            days_diff = (check_date - easter).days
            week_num = (days_diff // 7) + 1
            
            ordinals = ['', 'Easter', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh']
            if week_num == 1:
                return "Easter Day"
            elif week_num <= 7:
                return f"{ordinals[week_num]} Sunday of Easter"
        
        # Christmas season
        if season == "Christmas":
            return "Sunday after Christmas"
                
        return f"Sunday in the {season}"
        
    def get_calendar_data(self, year: int, month: int) -> Dict:
        """Get calendar data for a specific month"""
        cal_data = calendar.monthcalendar(year, month)
        today = date.today()
        
        calendar_info = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'liturgical_year': self.get_liturgical_year(datetime(year, month, 1)),
            'season': self.get_liturgical_season(datetime(year, month, 15)),
            'weeks': []
        }
        
        for week in cal_data:
            week_info = []
            for day in week:
                if day == 0:
                    week_info.append({
                        'day': 0,
                        'is_today': False,
                        'liturgical_info': None
                    })
                else:
                    cell_date = date(year, month, day)
                    liturgical_info = self.get_liturgical_info(cell_date)
                    
                    celebration = ""
                    # Check for feast day first (e.g., Pentecost, Easter) before generic Sunday name
                    if liturgical_info.get('feast_day'):
                        celebration = liturgical_info['feast_day']
                    elif liturgical_info['is_sunday']:
                        celebration = self.get_sunday_name(datetime.combine(cell_date, datetime.min.time()))
                    
                    week_info.append({
                        'day': day,
                        'date': cell_date.isoformat(),
                        'is_today': cell_date == today,
                        'liturgical_info': liturgical_info,
                        'celebration': celebration
                    })
            
            calendar_info['weeks'].append(week_info)
            
        return calendar_info
        
    def get_readings_for_date(self, date_str: str, service_type: str = 'eucharist') -> Dict[str, Any]:
        """Get readings for a specific date in OBS-compatible format"""
        try:
            # Parse date
            selected_date = datetime.fromisoformat(date_str)
            
            # Check if it's a Sunday or feast day
            liturgical_info = self.get_liturgical_info(selected_date.date())
            
            if not (liturgical_info['is_sunday'] or liturgical_info['feast_day']):
                return {}
            
            # Fetch readings with service type
            readings_data = self.liturgy_fetcher.fetch_daily_readings(selected_date, service_type=service_type)
            
            if not readings_data:
                return {}
            
            # Parse readings
            parsed_readings = self.scripture_parser.parse_readings(readings_data)
            
            # Return in the format expected by OBS controller
            return parsed_readings
            
        except Exception as e:
            print(f"Error getting readings for {date_str}: {e}")
            return {}

# Initialize the calendar
web_calendar = WebLiturgicalCalendar()

@app.route('/')
def index():
    """Main calendar page"""
    return render_template('calendar.html')

@app.route('/api/calendar/<int:year>/<int:month>')
def get_calendar(year, month):
    """API endpoint to get calendar data"""
    try:
        calendar_data = web_calendar.get_calendar_data(year, month)
        return jsonify(calendar_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/readings/<date_str>')
def get_readings(date_str):
    """API endpoint to get readings for a specific date"""
    try:
        # Parse date
        selected_date = datetime.fromisoformat(date_str)
        
        # Get service_type from query parameter (default to 'eucharist' for backward compatibility)
        service_type = request.args.get('service_type', 'eucharist').lower()
        
        # Check if it's a Sunday or feast day
        liturgical_info = web_calendar.get_liturgical_info(selected_date.date())
        
        if not (liturgical_info['is_sunday'] or liturgical_info['feast_day']):
            return jsonify({
                'has_readings': False,
                'message': 'No special readings for this date. Weekday readings follow the daily lectionary.',
                'liturgical_info': liturgical_info
            })
        
        # Fetch readings based on service type
        readings_data = web_calendar.liturgy_fetcher.fetch_daily_readings(selected_date, service_type=service_type)
        
        if not readings_data:
            return jsonify({
                'has_readings': False,
                'message': f'Unable to load {service_type} readings for this date.',
                'liturgical_info': liturgical_info
            })
        
        # Parse readings
        parsed_readings = web_calendar.scripture_parser.parse_readings(readings_data)
        
        # Calculate celebration name (same logic as get_calendar_data)
        celebration = ""
        if liturgical_info.get('feast_day'):
            celebration = liturgical_info['feast_day']
        elif liturgical_info['is_sunday']:
            celebration = web_calendar.get_sunday_name(selected_date)
        
        return jsonify({
            'has_readings': True,
            'date': date_str,
            'service_type': service_type,
            'liturgical_info': liturgical_info,
            'celebration': celebration if celebration else 'Unknown',
            'source': readings_data.get('source', 'Unknown'),
            'liturgical_year': readings_data.get('liturgical_year', 'Unknown'),
            'readings': parsed_readings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_to_obs', methods=['POST'])
def send_to_obs():
    """API endpoint to send readings to OBS"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        service_details = data.get('serviceDetails', {})
        
        # Check if config.ini exists
        import os
        if not os.path.exists('config.ini'):
            return jsonify({
                'success': False,
                'error': 'OBS configuration not found',
                'message': 'Please create a config.ini file with your OBS settings. Use obs_setup_guide.py to create one.'
            }), 400
        
        # Try to connect to OBS and send readings
        try:
            import configparser
            from obs_controller import OBSController
            
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            obs = OBSController(config)
            
            if not obs.connect():
                return jsonify({
                    'success': False,
                    'error': 'Could not connect to OBS',
                    'message': 'Make sure OBS Studio is running with WebSocket server enabled'
                }), 400
            
            # Get readings for the date
            calendar_instance = WebLiturgicalCalendar()
            readings = calendar_instance.get_readings_for_date(date_str)
            
            if readings:
                # Send readings to OBS
                scripture_success = obs.update_scripture_sources(readings)
                
                # Send service details to OBS if provided
                service_success = True
                if service_details:
                    service_success = obs.update_service_details(service_details)
                
                if scripture_success and service_success:
                    obs.disconnect()
                    return jsonify({
                        'success': True,
                        'message': f'Successfully sent readings and service details for {date_str} to OBS'
                    })
                elif scripture_success:
                    obs.disconnect()
                    return jsonify({
                        'success': True,
                        'message': f'Successfully sent readings for {date_str} to OBS (service details failed)'
                    })
                else:
                    obs.disconnect()
                    return jsonify({
                        'success': False,
                        'error': 'Failed to update some OBS sources',
                        'message': 'Check your scene and source names in config.ini'
                    }), 400
            else:
                obs.disconnect()
                return jsonify({
                    'success': False,
                    'error': 'No readings found',
                    'message': f'No readings available for {date_str}'
                }), 400
                
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'OBS controller not available',
                'message': 'OBS integration module not properly configured'
            }), 500
        except Exception as obs_error:
            return jsonify({
                'success': False,
                'error': f'OBS error: {str(obs_error)}',
                'message': 'Check your OBS configuration and connection'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Unexpected error occurred'
        }), 500

@app.route('/api/atem/connect', methods=['POST'])
def atem_connect():
    """API endpoint to connect to ATEM switcher"""
    try:
        import configparser
        from atem_controller import ATEMController
        
        if not os.path.exists('config.ini'):
            return jsonify({
                'success': False,
                'error': 'ATEM configuration not found',
                'message': 'Please configure ATEM settings in config.ini'
            }), 400
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            status = atem.get_status()
            atem.disconnect()  # Disconnect after getting status
            return jsonify({
                'success': True,
                'message': 'Successfully connected to ATEM',
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM',
                'message': 'Make sure ATEM is powered on and accessible on the network'
            }), 400
            
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'ATEM controller not available',
            'message': 'PyATEMMax library not installed'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error connecting to ATEM'
        }), 500

@app.route('/api/atem/status', methods=['GET'])
def atem_status():
    """API endpoint to get ATEM status"""
    try:
        import configparser
        from atem_controller import ATEMController
        
        if not os.path.exists('config.ini'):
            return jsonify({
                'success': False,
                'error': 'ATEM configuration not found'
            }), 400
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            status = atem.get_status()
            inputs = atem.list_inputs()
            atem.disconnect()
            return jsonify({
                'success': True,
                'status': status,
                'inputs': inputs
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/switch', methods=['POST'])
def atem_switch():
    """API endpoint to switch ATEM video source"""
    try:
        data = request.get_json()
        me = data.get('me', 0)
        input_num = data.get('input')
        
        if input_num is None:
            return jsonify({
                'success': False,
                'error': 'No input number provided'
            }), 400
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.switch_to_input(me, input_num)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Switched ME{me} to input {input_num}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to switch input'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/preview', methods=['POST'])
def atem_preview():
    """API endpoint to set ATEM preview source"""
    try:
        data = request.get_json()
        me = data.get('me', 0)
        input_num = data.get('input')
        
        if input_num is None:
            return jsonify({
                'success': False,
                'error': 'No input number provided'
            }), 400
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.set_preview_input(me, input_num)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Set ME{me} preview to input {input_num}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set preview'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/cut', methods=['POST'])
def atem_cut():
    """API endpoint to trigger ATEM cut transition"""
    try:
        data = request.get_json()
        me = data.get('me', 0)
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.trigger_cut(me)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Cut triggered on ME{me}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to trigger cut'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/auto', methods=['POST'])
def atem_auto():
    """API endpoint to trigger ATEM auto transition"""
    try:
        data = request.get_json()
        me = data.get('me', 0)
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.trigger_auto(me)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Auto transition triggered on ME{me}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to trigger auto'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/upload_media', methods=['POST'])
def atem_upload_media():
    """API endpoint to upload graphics to ATEM media pool"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        media_index = data.get('media_index', 0)
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No file path provided'
            }), 400
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.upload_media(file_path, media_index)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Uploaded {file_path} to media slot {media_index}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to upload media'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/atem/audio', methods=['POST'])
def atem_audio():
    """API endpoint to control ATEM audio"""
    try:
        data = request.get_json()
        channel = data.get('channel')
        volume = data.get('volume')
        
        if channel is None or volume is None:
            return jsonify({
                'success': False,
                'error': 'Channel and volume required'
            }), 400
        
        import configparser
        from atem_controller import ATEMController
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        atem = ATEMController(config)
        
        if atem.connect():
            success = atem.set_audio_volume(channel, volume)
            atem.disconnect()
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Set channel {channel} volume to {volume}dB'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set audio volume'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Could not connect to ATEM'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/service_details', methods=['POST'])
def save_service_details():
    """API endpoint to save service details for a specific date and service type"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        service_type = data.get('service_type', 'eucharist')  # Default to eucharist for backward compatibility
        details = data.get('details', {})
        
        # For now, store in a simple file-based system
        # In production, this would go to a database
        import json
        import os
        
        details_file = 'service_details.json'
        service_data = {}
        
        # Load existing service details
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r') as f:
                    service_data = json.load(f)
            except:
                service_data = {}
        
        # Save the new details with nested structure: service_data[date][service_type]
        if date_str not in service_data:
            service_data[date_str] = {}
        service_data[date_str][service_type] = details
        
        try:
            with open(details_file, 'w') as f:
                json.dump(service_data, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': f'Service details saved for {date_str} ({service_type})'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to save service details: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to process service details'
        }), 500

@app.route('/api/service_details/<date_str>', methods=['GET'])
def get_service_details(date_str):
    """API endpoint to get service details for a specific date and service type"""
    try:
        import json
        import os
        
        # Get service_type from query parameter (default to 'eucharist' for backward compatibility)
        service_type = request.args.get('service_type', 'eucharist')
        
        details_file = 'service_details.json'
        
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r') as f:
                    service_data = json.load(f)
                    # Handle both old format (direct date access) and new format (date + service_type)
                    if date_str in service_data:
                        if isinstance(service_data[date_str], dict) and service_type in service_data[date_str]:
                            # New format: service_data[date][service_type]
                            details = service_data[date_str][service_type]
                        else:
                            # Old format: service_data[date] - migrate to new format if needed
                            details = service_data[date_str]
                    else:
                        details = {}
                    
                return jsonify({
                    'success': True,
                    'details': details
                })
            except:
                return jsonify({
                    'success': True,
                    'details': {}
                })
        else:
            return jsonify({
                'success': True,
                'details': {}
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export_readings', methods=['POST'])
def export_readings():
    """Export readings to individual text files in a ZIP archive"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        service_details = data.get('serviceDetails', {})
        
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'No date provided'
            }), 400
        
        # Parse date for folder naming
        selected_date = datetime.fromisoformat(date_str)
        date_folder_name = selected_date.strftime("%Y-%m-%d")
        
        # Get readings for the date
        calendar_instance = WebLiturgicalCalendar()
        readings = calendar_instance.get_readings_for_date(date_str)
        
        if not readings:
            return jsonify({
                'success': False,
                'error': 'No readings available for this date'
            }), 400
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create individual text files for each reading
            for reading_type, reading_data in readings.items():
                # Clean reading type name for filename
                base_name = reading_type.replace('_', ' ').title()
                
                # Create text file with formatted scripture text (50 char width)
                text_filename = f"{base_name}.txt"
                text_filepath = f"{date_folder_name}/{text_filename}"
                raw_text = reading_data.get('text', '')
                if raw_text:
                    # Format text with word wrapping at 50 characters while preserving paragraph structure
                    formatted_text = format_text_with_paragraphs(raw_text, width=50)
                else:
                    formatted_text = raw_text
                zip_file.writestr(text_filepath, formatted_text)
                
                # Create reference file with formatted reference
                ref_filename = f"{base_name} Reference.txt"
                ref_filepath = f"{date_folder_name}/{ref_filename}"
                raw_ref = reading_data.get('reference', '')
                if raw_ref:
                    # Format reference with word wrapping at 50 characters
                    formatted_ref = textwrap.fill(raw_ref, width=50, break_long_words=False, break_on_hyphens=False)
                else:
                    formatted_ref = raw_ref
                zip_file.writestr(ref_filepath, formatted_ref)
            
            # Create individual service detail files if provided
            if service_details:
                # Individual hymn files with text from Hymnary.org
                if service_details.get('openingHymn'):
                    # Create title file
                    formatted_hymn = textwrap.fill(service_details['openingHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Opening Hymn.txt", formatted_hymn)
                    
                    # Create hymn text file from Hymnary.org
                    hymn_text = fetch_hymn_text_from_hymnary(service_details['openingHymn'])
                    formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                    zip_file.writestr(f"{date_folder_name}/Opening Hymn Text.txt", formatted_hymn_text)
                
                if service_details.get('sequenceHymn'):
                    # Create title file
                    formatted_hymn = textwrap.fill(service_details['sequenceHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Sequence Hymn.txt", formatted_hymn)
                    
                    # Create hymn text file from Hymnary.org
                    hymn_text = fetch_hymn_text_from_hymnary(service_details['sequenceHymn'])
                    formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                    zip_file.writestr(f"{date_folder_name}/Sequence Hymn Text.txt", formatted_hymn_text)
                
                if service_details.get('communionMotet'):
                    formatted_motet = textwrap.fill(service_details['communionMotet'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Communion Motet.txt", formatted_motet)
                
                if service_details.get('closingHymn'):
                    # Create title file
                    formatted_hymn = textwrap.fill(service_details['closingHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Closing Hymn.txt", formatted_hymn)
                    
                    # Create hymn text file from Hymnary.org
                    hymn_text = fetch_hymn_text_from_hymnary(service_details['closingHymn'])
                    formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                    zip_file.writestr(f"{date_folder_name}/Closing Hymn Text.txt", formatted_hymn_text)
                
                # Individual musician files
                if service_details.get('organistName'):
                    formatted_organist = textwrap.fill(service_details['organistName'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Organist.txt", formatted_organist)
                
                if service_details.get('preludeTitle'):
                    formatted_prelude = textwrap.fill(service_details['preludeTitle'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Prelude Title.txt", formatted_prelude)
                
                if service_details.get('postludeTitle'):
                    formatted_postlude = textwrap.fill(service_details['postludeTitle'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Postlude Title.txt", formatted_postlude)
                
                # Individual clergy files
                if service_details.get('preacherName'):
                    formatted_preacher = textwrap.fill(service_details['preacherName'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Preacher.txt", formatted_preacher)
                
                if service_details.get('presiderName'):
                    formatted_presider = textwrap.fill(service_details['presiderName'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Presider.txt", formatted_presider)
            
            # Create summary file
            summary_content = []
            summary_content.append(f"Liturgical Readings Summary - {selected_date.strftime('%B %d, %Y')}")
            summary_content.append("=" * 60)
            summary_content.append("")
            
            for reading_type, reading_data in readings.items():
                summary_content.append(f"{reading_type.replace('_', ' ').title()}: {reading_data.get('reference', 'No reference')}")
            
            summary_content.append("")
            summary_content.append(f"Total readings exported: {len(readings)}")
            summary_content.append(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            zip_file.writestr(f"{date_folder_name}/Summary.txt", "\n".join(summary_content))
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=f"liturgical_readings_{date_folder_name}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to export readings'
        }), 500

@app.route('/api/branding', methods=['GET'])
def get_branding():
    """Returns current branding configuration"""
    try:
        config = load_branding_config()
        
        if config.get('logo_path'):
            config['logo_url'] = f"/uploads/branding/{os.path.basename(config['logo_path'])}"
        else:
            config['logo_url'] = None
            
        return jsonify(config)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/branding', methods=['POST'])
def update_branding():
    """Updates branding configuration (church name, colors, fonts)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        current_config = load_branding_config()
        
        if 'church_name' in data:
            if len(data['church_name']) > 100:
                return jsonify({
                    'success': False,
                    'error': 'Church name must be 100 characters or less'
                }), 400
            current_config['church_name'] = data['church_name']
        
        if 'custom_colors' in data:
            color_pattern = r'^#[0-9A-Fa-f]{6}$'
            colors = data['custom_colors']
            
            if 'enabled' in colors:
                current_config['custom_colors']['enabled'] = colors['enabled']
            
            if colors.get('enabled'):
                if 'primary' in colors:
                    if not re.match(color_pattern, colors['primary']):
                        return jsonify({
                            'success': False,
                            'error': 'Invalid primary color format'
                        }), 400
                    current_config['custom_colors']['primary'] = colors['primary']
                
                if 'accent' in colors:
                    if not re.match(color_pattern, colors['accent']):
                        return jsonify({
                            'success': False,
                            'error': 'Invalid accent color format'
                        }), 400
                    current_config['custom_colors']['accent'] = colors['accent']
                
                if 'background' in colors:
                    if not re.match(color_pattern, colors['background']):
                        return jsonify({
                            'success': False,
                            'error': 'Invalid background color format'
                        }), 400
                    current_config['custom_colors']['background'] = colors['background']
        
        if 'custom_font' in data:
            if 'enabled' in data['custom_font']:
                current_config['custom_font']['enabled'] = data['custom_font']['enabled']
            if 'family' in data['custom_font']:
                current_config['custom_font']['family'] = data['custom_font']['family']
        
        save_branding_config(current_config)
        
        return jsonify({
            'success': True,
            'message': 'Branding configuration updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/branding/logo', methods=['POST'])
def upload_logo():
    """Handles logo file upload"""
    try:
        if 'logo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['logo']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not file.content_type in ['image/png', 'image/jpeg', 'image/jpg']:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only PNG and JPEG are allowed'
            }), 400
        
        file_content = file.read()
        file_size = len(file_content)
        
        if file_size > 2 * 1024 * 1024:
            return jsonify({
                'success': False,
                'error': 'File size exceeds 2MB limit'
            }), 400
        
        try:
            img = Image.open(io.BytesIO(file_content))
            img.verify()
        except Exception:
            return jsonify({
                'success': False,
                'error': 'Invalid image file'
            }), 400
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4()}.{file_ext}"
        upload_path = os.path.join('uploads', 'branding', new_filename)
        
        config = load_branding_config()
        
        if config.get('logo_path') and os.path.exists(config['logo_path']):
            try:
                os.remove(config['logo_path'])
            except Exception as e:
                print(f"Warning: Could not delete old logo: {e}")
        
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        with open(upload_path, 'wb') as f:
            f.write(file_content)
        
        config['logo_path'] = upload_path
        save_branding_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Logo uploaded successfully',
            'logo_url': f"/uploads/branding/{new_filename}"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/branding/logo', methods=['DELETE'])
def delete_logo():
    """Removes logo"""
    try:
        config = load_branding_config()
        
        if config.get('logo_path') and os.path.exists(config['logo_path']):
            try:
                os.remove(config['logo_path'])
            except Exception as e:
                print(f"Warning: Could not delete logo file: {e}")
        
        config['logo_path'] = None
        save_branding_config(config)
        
        return jsonify({
            'success': True,
            'message': 'Logo removed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/uploads/branding/<filename>')
def serve_branding_logo(filename):
    """Serves logo files"""
    try:
        return send_from_directory('uploads/branding', filename)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Logo file not found'
        }), 404

def get_liturgical_season_colors_by_name(season: str) -> Dict[str, tuple]:
    """Get liturgical season colors by season name directly
    
    Args:
        season: Liturgical season name (advent, christmas, lent, easter, etc.)
    
    Returns:
        Dictionary of color tuples for the specified season
    """
    # Color mapping with RGBA tuples (R, G, B, A)
    color_schemes = {
        'advent': {
            'background': (65, 105, 225, 230),   # Royal Blue with opacity (default)
            'accent': (65, 105, 225, 255),       # Royal Blue solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'advent_blue': {
            'background': (65, 105, 225, 230),   # Royal Blue with opacity
            'accent': (65, 105, 225, 255),       # Royal Blue solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'advent_purple': {
            'background': (75, 0, 130, 230),     # Deep purple with opacity
            'accent': (102, 51, 153, 255),       # Purple solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'advent_pink': {
            'background': (219, 112, 147, 230),  # Rose/Pink with opacity
            'accent': (219, 112, 147, 255),      # Rose/Pink solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'gaudete': {
            'background': (219, 112, 147, 230),  # Rose/Pink with opacity
            'accent': (219, 112, 147, 255),      # Rose/Pink solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'christmas': {
            'background': (255, 255, 255, 230),  # White with opacity
            'accent': (212, 175, 55, 255),       # Gold
            'title': (212, 175, 55, 255),        # Gold
            'text': (60, 60, 60, 255)            # Dark gray
        },
        'season_after_epiphany': {
            'background': (0, 100, 0, 230),      # Green with opacity
            'accent': (0, 150, 0, 255),          # Bright green
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'lent': {
            'background': (75, 0, 130, 230),     # Deep purple with opacity
            'accent': (102, 51, 153, 255),       # Purple
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'easter': {
            'background': (255, 255, 255, 230),  # White with opacity
            'accent': (212, 175, 55, 255),       # Gold
            'title': (184, 134, 11, 255),        # Dark gold
            'text': (60, 60, 60, 255)            # Dark gray
        },
        'pentecost': {
            'background': (170, 0, 0, 230),      # Red with opacity
            'accent': (220, 20, 60, 255),        # Crimson
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'season_after_pentecost': {
            'background': (0, 128, 0, 230),      # Green with opacity
            'accent': (34, 139, 34, 255),        # Forest green
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        }
    }
    
    return color_schemes.get(season, color_schemes['season_after_pentecost'])

def get_liturgical_season_colors(date_str: Optional[str] = None) -> Dict[str, tuple]:
    """Get liturgical season colors for lower third graphics"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    month = date_obj.month
    day = date_obj.day
    
    # Determine liturgical season (Episcopal terminology)
    season = 'season_after_pentecost'  # default
    
    if month == 12 and day >= 25:
        season = 'christmas'
    elif month == 1 and day <= 6:
        season = 'christmas'
    elif month == 1 and day > 6:
        season = 'season_after_epiphany'
    elif month in [2, 3] or (month == 4 and day < 15):
        # Rough Lent/Easter season (needs refinement for actual Easter dates)
        season = 'lent'
    elif month in [4, 5, 6] and (month > 4 or day >= 15):
        season = 'easter'
    elif (month == 11 and day >= 27) or (month == 12 and day < 25):
        # Check for Gaudete Sunday (3rd Sunday of Advent) - use pink/rose
        calendar_instance = WebLiturgicalCalendar()
        if calendar_instance.is_gaudete_sunday(date_obj.date()):
            season = 'gaudete'
        else:
            season = 'advent'
    else:
        season = 'season_after_pentecost'
    
    # Use the helper function to get colors
    return get_liturgical_season_colors_by_name(season)

def get_theme(theme_name: str, date_str: Optional[str] = None, liturgical_season: Optional[str] = None) -> Dict[str, tuple]:
    """Get theme colors for graphics generation
    
    Args:
        theme_name: Theme name ('liturgical' or 'concert')
        date_str: Date string for liturgical season detection (used only with 'liturgical' theme)
        liturgical_season: Optional liturgical season override (used only with 'liturgical' theme)
    
    Returns:
        Dictionary of color tuples for the specified theme
    """
    if theme_name == 'concert':
        return {
            'background': (128, 128, 128, 217),
            'accent': (128, 128, 128, 255),
            'title': (255, 255, 255, 255),
            'text': (255, 255, 255, 255)
        }
    elif theme_name == 'liturgical':
        if liturgical_season:
            return get_liturgical_season_colors_by_name(liturgical_season)
        else:
            return get_liturgical_season_colors(date_str)
    else:
        return get_liturgical_season_colors(date_str)

def overlay_logo(image: Image.Image, logo_path: Optional[str], position: str = 'top-right', max_width: int = 220) -> Image.Image:
    """
    Overlay logo on image
    
    Args:
        image: PIL Image to overlay on
        logo_path: Path to logo file
        position: 'top-right', 'top-left', 'bottom-right', 'bottom-left'
        max_width: Maximum width for logo
        
    Returns:
        Modified PIL Image with logo overlayed
    """
    if not logo_path or not os.path.exists(logo_path):
        return image
    
    try:
        logo = Image.open(logo_path).convert('RGBA')
        
        original_width, original_height = logo.size
        aspect_ratio = original_height / original_width
        
        new_width = min(max_width, original_width)
        new_height = int(new_width * aspect_ratio)
        
        logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        margin = 30
        img_width, img_height = image.size
        
        if position == 'top-right':
            x = img_width - new_width - margin
            y = margin
        elif position == 'top-left':
            x = margin
            y = margin
        elif position == 'bottom-right':
            x = img_width - new_width - margin
            y = img_height - new_height - margin
        elif position == 'bottom-left':
            x = margin
            y = img_height - new_height - margin
        else:
            x = img_width - new_width - margin
            y = margin
        
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        temp_image = Image.new('RGBA', image.size, (0, 0, 0, 0))
        temp_image.paste(image, (0, 0))
        temp_image.paste(logo, (x, y), logo)
        
        return temp_image
    except Exception as e:
        print(f"Error overlaying logo: {e}")
        return image

def create_lower_third(reading_type: str, reference: str, date_str: Optional[str] = None, width: int = 1920, height: int = 1080, is_funeral: bool = False, liturgical_season: Optional[str] = None, theme: str = 'liturgical', branding: Optional[Dict[str, Any]] = None, style: str = 'classic') -> Image.Image:
    """Create a lower third graphic for broadcast use with theme-based colors and banner-style design
    
    Args:
        reading_type: Type of reading (e.g., 'gospel', 'first_reading')
        reference: Scripture reference or text
        date_str: Date string for liturgical season detection
        width: Image width in pixels
        height: Image height in pixels
        is_funeral: If True, use black background with white text instead of theme colors
        liturgical_season: Optional liturgical season override (e.g., 'advent', 'christmas', 'lent')
        theme: Theme name ('liturgical' or 'concert'), defaults to 'liturgical'
        branding: Optional branding configuration dictionary
        style: Visual style name ('classic', 'minimal', 'modern_glass', 'bold_banner', 'elegant')
    """
    if branding is None:
        branding = load_branding_config()
    # Create image with transparent background (RGBA mode)
    img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Determine theme colors or use funeral colors
    if is_funeral:
        # Funeral: black background with white text
        liturgical_colors = {
            'background': (0, 0, 0, 255),        # Black
            'accent': (40, 40, 40, 255),         # Very dark gray
            'title': (255, 255, 255, 255),       # White
            'text': (255, 255, 255, 255)         # White
        }
    else:
        # Use theme system
        liturgical_colors = get_theme(theme, date_str=date_str, liturgical_season=liturgical_season)
    
    # Load Stack Sans fonts
    title_font = load_stack_sans_font(60, bold=True)
    ref_font = load_stack_sans_font(45, bold=False)
    
    # Format reading type (remove underscores, title case)
    formatted_type = reading_type.replace('_', ' ').title()
    
    # Check if this is a hymn/music item (swap font sizes to emphasize hymn name)
    is_hymn = any(keyword in formatted_type for keyword in ['Hymn', 'Motet', 'Offertory', 'Prelude', 'Postlude'])
    
    if is_hymn:
        # For hymns: emphasize the hymn name (in large font) over the label (in small font)
        top_text = reference  # Hymn name/number (large)
        bottom_text = formatted_type  # Label like "Sequence Hymn" (small)
        top_font = title_font  # 60pt
        bottom_font = ref_font  # 45pt
    else:
        # For readings: emphasize the reading type (in large font) over the reference (in small font)
        top_text = formatted_type  # Reading type like "Gospel" (large)
        bottom_text = reference  # Scripture reference (small)
        top_font = title_font  # 60pt
        bottom_font = ref_font  # 45pt
    
    # Calculate text dimensions to determine background height
    top_bbox = draw.textbbox((0, 0), top_text, font=top_font)
    bottom_bbox = draw.textbbox((0, 0), bottom_text, font=bottom_font)
    
    # Calculate heights
    top_height = top_bbox[3] - top_bbox[1]
    bottom_height = bottom_bbox[3] - bottom_bbox[1]
    
    # Padding values
    top_padding = 40
    text_spacing = 20
    bottom_padding = 40
    
    # Calculate total background height needed
    background_height = top_padding + top_height + text_spacing + bottom_height + bottom_padding
    
    # Position lower third lower on screen (at 5/6 of the image height)
    lower_third_start = int(height * 5 / 6)
    background_end = height  # Go all the way to the bottom of the image
    
    # === RENDER BACKGROUND STYLE ===
    # Get the appropriate style renderer from registry (default to classic if not found)
    style_renderer = LOWER_THIRD_STYLE_REGISTRY.get(style.lower(), _render_lower_third_classic)
    style_renderer(draw, width, height, lower_third_start, background_end, liturgical_colors)
    
    # Text starts at approximately 1/5 of the page from the left (about 384px on 1920px width)
    text_indent = int(width / 5)
    
    # Draw top text (large font) - indented to start at 1/5 from left
    top_y = lower_third_start + top_padding
    
    # Black outline for top text
    outline_width = 4
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((text_indent + offset_x, top_y + offset_y), top_text, fill=(0, 0, 0, 255), font=top_font)
    # Main top text
    draw.text((text_indent, top_y), top_text, fill=(255, 255, 255, 255), font=top_font)
    
    # Draw bottom text (small font) below top text
    bottom_y = top_y + top_height + text_spacing
    
    # Black outline for bottom text
    outline_width = 3
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((text_indent + offset_x, bottom_y + offset_y), bottom_text, fill=(0, 0, 0, 255), font=bottom_font)
    # Main bottom text
    draw.text((text_indent, bottom_y), bottom_text, fill=(241, 241, 241, 255), font=bottom_font)
    
    logo_path = branding.get('logo_path') if branding else None
    img = overlay_logo(img, logo_path, position='bottom-left', max_width=120)
    
    if style.lower() == 'christmas_trinity':
        _render_lower_third_christmas_trinity_with_image(img, draw, width, height, lower_third_start, background_end)
    
    return img

def create_blank_lower_third(date_str: Optional[str] = None, width: int = 1920, height: int = 1080, is_funeral: bool = False, liturgical_season: Optional[str] = None, style: str = 'classic') -> Image.Image:
    """Create a blank lower third template for manual use with liturgical season colors
    
    This generates a lower third with all the design elements but no text,
    allowing users to manually add content for custom service elements.
    
    Args:
        date_str: Date string for liturgical season detection
        width: Image width in pixels
        height: Image height in pixels
        is_funeral: If True, use black background instead of liturgical colors
        liturgical_season: Optional liturgical season override (e.g., 'advent', 'christmas', 'lent')
        style: Visual style name ('classic', 'minimal', 'modern_glass', 'bold_banner', 'elegant')
    """
    # Create image with transparent background (RGBA mode)
    img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Determine liturgical season colors or use funeral colors
    if is_funeral:
        # Funeral: black background with white text
        liturgical_colors = {
            'background': (0, 0, 0, 255),
            'accent': (40, 40, 40, 255),
            'title': (255, 255, 255, 255),
            'text': (255, 255, 255, 255)
        }
    elif liturgical_season:
        # Use explicitly specified liturgical season
        liturgical_colors = get_liturgical_season_colors_by_name(liturgical_season)
    else:
        # Auto-detect from date
        liturgical_colors = get_liturgical_season_colors(date_str)
    
    # Position lower third lower on screen (at 5/6 of the image height)
    lower_third_start = int(height * 5 / 6)
    background_end = height
    
    # === RENDER BACKGROUND STYLE ===
    # Get the appropriate blank style renderer from registry (default to classic if not found)
    style_renderer = BLANK_LOWER_THIRD_STYLE_REGISTRY.get(style.lower(), _render_blank_lower_third_classic)
    style_renderer(draw, width, height, lower_third_start, background_end, liturgical_colors)
    
    if style.lower() == 'christmas_trinity':
        _render_lower_third_christmas_trinity_with_image(img, draw, width, height, lower_third_start, background_end)
    
    # No text drawn - this is a blank template
    
    return img


# =============================================================================
# LOWER THIRD STYLE RENDERER FUNCTIONS
# =============================================================================
# Each renderer draws directly on the draw object and returns nothing.
# Parameters: draw, width, height, lower_third_start, background_end, liturgical_colors

def _render_lower_third_classic(draw: ImageDraw.Draw, width: int, height: int, 
                                 lower_third_start: int, background_end: int, 
                                 liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Classic style - angled layers, gradients, diagonal stripes (original design)"""
    bg_r, bg_g, bg_b, bg_a = liturgical_colors['background']
    accent_r, accent_g, accent_b, accent_a = liturgical_colors['accent']
    
    very_dark_r = int(bg_r * 0.4)
    very_dark_g = int(bg_g * 0.4)
    very_dark_b = int(bg_b * 0.4)
    
    dark_r = int(bg_r * 0.65)
    dark_g = int(bg_g * 0.65)
    dark_b = int(bg_b * 0.65)
    
    mid_r = int(bg_r * 0.85)
    mid_g = int(bg_g * 0.85)
    mid_b = int(bg_b * 0.85)
    
    light_r = min(255, int(bg_r * 1.1))
    light_g = min(255, int(bg_g * 1.1))
    light_b = min(255, int(bg_b * 1.1))
    
    very_light_r = min(255, int(bg_r * 1.25))
    very_light_g = min(255, int(bg_g * 1.25))
    very_light_b = min(255, int(bg_b * 1.25))
    
    gradient_steps = 120
    for i in range(gradient_steps):
        x_pos = int((width * i) / gradient_steps)
        next_x = int((width * (i + 1)) / gradient_steps)
        
        factor = i / gradient_steps
        r = int(dark_r + (mid_r - dark_r) * factor)
        g = int(dark_g + (mid_g - dark_g) * factor)
        b = int(dark_b + (mid_b - dark_b) * factor)
        
        draw.rectangle(
            [x_pos, lower_third_start, next_x, background_end],
            fill=(r, g, b, 255)
        )
    
    left_panel_width = 380
    angle_cut = 45
    draw.polygon([
        (0, lower_third_start),
        (left_panel_width, lower_third_start),
        (left_panel_width - angle_cut, background_end),
        (0, background_end)
    ], fill=(light_r, light_g, light_b, 220))
    
    accent_width_1 = 180
    draw.polygon([
        (0, lower_third_start),
        (accent_width_1, lower_third_start),
        (accent_width_1 - 35, background_end),
        (0, background_end)
    ], fill=(very_light_r, very_light_g, very_light_b, 180))
    
    accent_width_2 = 120
    draw.polygon([
        (0, lower_third_start),
        (accent_width_2, lower_third_start),
        (accent_width_2 - 28, background_end),
        (0, background_end)
    ], fill=(accent_r, accent_g, accent_b, 255))
    
    right_panel_start = width - 280
    right_angle_cut = 38
    draw.polygon([
        (right_panel_start, lower_third_start),
        (width, lower_third_start),
        (width, background_end),
        (right_panel_start + right_angle_cut, background_end)
    ], fill=(very_dark_r, very_dark_g, very_dark_b, 200))
    
    right_panel_2 = width - 160
    draw.polygon([
        (right_panel_2, lower_third_start + 8),
        (width, lower_third_start),
        (width, background_end),
        (right_panel_2 + 20, background_end - 8)
    ], fill=(dark_r, dark_g, dark_b, 160))
    
    stripe_width = 7
    top_slope = 5
    draw.polygon([
        (0, lower_third_start),
        (width, lower_third_start + top_slope),
        (width, lower_third_start + top_slope + stripe_width),
        (0, lower_third_start + stripe_width)
    ], fill=(accent_r, accent_g, accent_b, 255))
    
    bottom_slope = 5
    draw.polygon([
        (0, background_end - stripe_width),
        (width, background_end - bottom_slope - stripe_width),
        (width, background_end - bottom_slope),
        (0, background_end)
    ], fill=(accent_r, accent_g, accent_b, 240))
    
    diagonal_1_start = 500
    diagonal_1_width = 80
    draw.polygon([
        (diagonal_1_start, lower_third_start),
        (diagonal_1_start + diagonal_1_width, lower_third_start),
        (diagonal_1_start + diagonal_1_width - 50, background_end),
        (diagonal_1_start - 50, background_end)
    ], fill=(very_light_r, very_light_g, very_light_b, 100))
    
    diagonal_2_start = 900
    diagonal_2_width = 100
    draw.polygon([
        (diagonal_2_start, lower_third_start),
        (diagonal_2_start + diagonal_2_width, lower_third_start),
        (diagonal_2_start + diagonal_2_width - 60, background_end),
        (diagonal_2_start - 60, background_end)
    ], fill=(light_r, light_g, light_b, 90))


def _render_lower_third_minimal(draw: ImageDraw.Draw, width: int, height: int, 
                                 lower_third_start: int, background_end: int, 
                                 liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Minimal style - clean single horizontal bar with thin accent line at top"""
    bg_r, bg_g, bg_b, bg_a = liturgical_colors['background']
    accent_r, accent_g, accent_b, accent_a = liturgical_colors['accent']
    
    bar_alpha = 200
    draw.rectangle(
        [0, lower_third_start, width, background_end],
        fill=(bg_r, bg_g, bg_b, bar_alpha)
    )
    
    accent_line_height = 3
    draw.rectangle(
        [0, lower_third_start, width, lower_third_start + accent_line_height],
        fill=(accent_r, accent_g, accent_b, 255)
    )


def _render_lower_third_modern_glass(draw: ImageDraw.Draw, width: int, height: int, 
                                      lower_third_start: int, background_end: int, 
                                      liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Modern Glass style - frosted glass/glassmorphism effect with soft rounded edges simulation"""
    bg_r, bg_g, bg_b, bg_a = liturgical_colors['background']
    accent_r, accent_g, accent_b, accent_a = liturgical_colors['accent']
    
    glass_alpha = 217
    glass_r = min(255, int(bg_r * 0.9 + 25))
    glass_g = min(255, int(bg_g * 0.9 + 25))
    glass_b = min(255, int(bg_b * 0.9 + 25))
    
    corner_radius = 12
    margin = 20
    
    glass_left = margin
    glass_right = width - margin
    glass_top = lower_third_start + 5
    glass_bottom = background_end - 10
    
    draw.rectangle(
        [glass_left + corner_radius, glass_top, glass_right - corner_radius, glass_bottom],
        fill=(glass_r, glass_g, glass_b, glass_alpha)
    )
    draw.rectangle(
        [glass_left, glass_top + corner_radius, glass_right, glass_bottom - corner_radius],
        fill=(glass_r, glass_g, glass_b, glass_alpha)
    )
    
    draw.ellipse([glass_left, glass_top, glass_left + corner_radius * 2, glass_top + corner_radius * 2],
                 fill=(glass_r, glass_g, glass_b, glass_alpha))
    draw.ellipse([glass_right - corner_radius * 2, glass_top, glass_right, glass_top + corner_radius * 2],
                 fill=(glass_r, glass_g, glass_b, glass_alpha))
    draw.ellipse([glass_left, glass_bottom - corner_radius * 2, glass_left + corner_radius * 2, glass_bottom],
                 fill=(glass_r, glass_g, glass_b, glass_alpha))
    draw.ellipse([glass_right - corner_radius * 2, glass_bottom - corner_radius * 2, glass_right, glass_bottom],
                 fill=(glass_r, glass_g, glass_b, glass_alpha))
    
    frost_steps = 8
    for i in range(frost_steps):
        frost_alpha = int(30 - (i * 3))
        frost_offset = i * 2
        if frost_alpha > 0:
            draw.rectangle(
                [glass_left + frost_offset, glass_top + frost_offset, 
                 glass_right - frost_offset, glass_top + 20],
                fill=(255, 255, 255, frost_alpha)
            )
    
    border_alpha = 150
    lighter_r = min(255, glass_r + 40)
    lighter_g = min(255, glass_g + 40)
    lighter_b = min(255, glass_b + 40)
    
    draw.rectangle(
        [glass_left + corner_radius, glass_top, glass_right - corner_radius, glass_top + 2],
        fill=(lighter_r, lighter_g, lighter_b, border_alpha)
    )
    draw.rectangle(
        [glass_left + corner_radius, glass_bottom - 2, glass_right - corner_radius, glass_bottom],
        fill=(accent_r, accent_g, accent_b, 180)
    )


def _render_lower_third_bold_banner(draw: ImageDraw.Draw, width: int, height: int, 
                                     lower_third_start: int, background_end: int, 
                                     liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Bold Banner style - full-width solid color block, strong typography, no angles"""
    bg_r, bg_g, bg_b, bg_a = liturgical_colors['background']
    accent_r, accent_g, accent_b, accent_a = liturgical_colors['accent']
    
    draw.rectangle(
        [0, lower_third_start, width, background_end],
        fill=(bg_r, bg_g, bg_b, 255)
    )
    
    accent_stripe_height = 5
    draw.rectangle(
        [0, lower_third_start, width, lower_third_start + accent_stripe_height],
        fill=(accent_r, accent_g, accent_b, 255)
    )


def _render_lower_third_elegant(draw: ImageDraw.Draw, width: int, height: int, 
                                 lower_third_start: int, background_end: int, 
                                 liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Elegant style - thin accent lines top and bottom, subtle vertical gradient, refined look"""
    bg_r, bg_g, bg_b, bg_a = liturgical_colors['background']
    accent_r, accent_g, accent_b, accent_a = liturgical_colors['accent']
    
    bar_height = background_end - lower_third_start
    gradient_steps = bar_height
    
    lighter_r = min(255, int(bg_r * 1.15))
    lighter_g = min(255, int(bg_g * 1.15))
    lighter_b = min(255, int(bg_b * 1.15))
    
    darker_r = int(bg_r * 0.85)
    darker_g = int(bg_g * 0.85)
    darker_b = int(bg_b * 0.85)
    
    for i in range(gradient_steps):
        y_pos = lower_third_start + i
        
        if i < gradient_steps // 2:
            factor = i / (gradient_steps // 2)
            r = int(lighter_r + (bg_r - lighter_r) * factor)
            g = int(lighter_g + (bg_g - lighter_g) * factor)
            b = int(lighter_b + (bg_b - lighter_b) * factor)
        else:
            factor = (i - gradient_steps // 2) / (gradient_steps // 2)
            r = int(bg_r + (darker_r - bg_r) * factor)
            g = int(bg_g + (darker_g - bg_g) * factor)
            b = int(bg_b + (darker_b - bg_b) * factor)
        
        draw.line([(0, y_pos), (width, y_pos)], fill=(r, g, b, 230))
    
    line_height = 2
    draw.rectangle(
        [0, lower_third_start, width, lower_third_start + line_height],
        fill=(accent_r, accent_g, accent_b, 255)
    )
    draw.rectangle(
        [0, background_end - line_height, width, background_end],
        fill=(accent_r, accent_g, accent_b, 255)
    )


def _render_lower_third_christmas_trinity(draw: ImageDraw.Draw, width: int, height: int, 
                                           lower_third_start: int, background_end: int, 
                                           liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Christmas Trinity style - rich gold and burgundy with Trinity Church building graphic
    
    Special branded style for Christmas season featuring the Trinity Church illustration,
    deep gold gradients, burgundy accents, and festive Christmas liturgical theming.
    """
    gold_primary = (212, 175, 55)
    gold_light = (245, 212, 100)
    gold_dark = (160, 130, 40)
    burgundy = (128, 0, 32)
    burgundy_dark = (80, 0, 20)
    cream = (255, 248, 235)
    
    bar_height = background_end - lower_third_start
    gradient_steps = 80
    for i in range(gradient_steps):
        x_pos = int((width * i) / gradient_steps)
        next_x = int((width * (i + 1)) / gradient_steps)
        
        factor = i / gradient_steps
        r = int(gold_dark[0] + (gold_primary[0] - gold_dark[0]) * factor)
        g = int(gold_dark[1] + (gold_primary[1] - gold_dark[1]) * factor)
        b = int(gold_dark[2] + (gold_primary[2] - gold_dark[2]) * factor)
        
        draw.rectangle(
            [x_pos, lower_third_start, next_x, background_end],
            fill=(r, g, b, 245)
        )
    
    left_panel_width = 350
    angle_cut = 50
    draw.polygon([
        (0, lower_third_start),
        (left_panel_width, lower_third_start),
        (left_panel_width - angle_cut, background_end),
        (0, background_end)
    ], fill=(burgundy[0], burgundy[1], burgundy[2], 255))
    
    accent_width = 140
    draw.polygon([
        (0, lower_third_start),
        (accent_width, lower_third_start),
        (accent_width - 32, background_end),
        (0, background_end)
    ], fill=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 255))
    
    highlight_width = 80
    draw.polygon([
        (0, lower_third_start),
        (highlight_width, lower_third_start),
        (highlight_width - 18, background_end),
        (0, background_end)
    ], fill=(gold_light[0], gold_light[1], gold_light[2], 180))
    
    right_panel_start = width - 320
    draw.polygon([
        (right_panel_start, lower_third_start),
        (width, lower_third_start),
        (width, background_end),
        (right_panel_start + 45, background_end)
    ], fill=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 200))
    
    right_accent_start = width - 200
    draw.polygon([
        (right_accent_start, lower_third_start + 5),
        (width, lower_third_start),
        (width, background_end),
        (right_accent_start + 25, background_end - 5)
    ], fill=(burgundy[0], burgundy[1], burgundy[2], 180))
    
    stripe_height = 6
    draw.polygon([
        (0, lower_third_start),
        (width, lower_third_start + 4),
        (width, lower_third_start + stripe_height + 4),
        (0, lower_third_start + stripe_height)
    ], fill=(gold_light[0], gold_light[1], gold_light[2], 255))
    
    draw.polygon([
        (0, background_end - stripe_height),
        (width, background_end - stripe_height - 4),
        (width, background_end - 4),
        (0, background_end)
    ], fill=(gold_light[0], gold_light[1], gold_light[2], 230))
    
    inner_stripe_y = lower_third_start + stripe_height + 2
    draw.rectangle(
        [0, inner_stripe_y, width, inner_stripe_y + 2],
        fill=(burgundy[0], burgundy[1], burgundy[2], 200)
    )
    
    star_center_x = left_panel_width - 70
    star_center_y = lower_third_start + bar_height // 2
    star_size = 18
    for i in range(8):
        angle = i * 45
        import math
        rad = math.radians(angle)
        end_x = star_center_x + int(star_size * math.cos(rad))
        end_y = star_center_y + int(star_size * math.sin(rad))
        draw.line([(star_center_x, star_center_y), (end_x, end_y)], 
                  fill=(gold_light[0], gold_light[1], gold_light[2], 255), width=2)
    draw.ellipse([star_center_x - 6, star_center_y - 6, star_center_x + 6, star_center_y + 6],
                 fill=(cream[0], cream[1], cream[2], 255))


def _render_lower_third_christmas_trinity_with_image(img: Image.Image, draw: ImageDraw.Draw, 
                                                      width: int, height: int, 
                                                      lower_third_start: int, background_end: int) -> None:
    """Overlay Trinity Church building graphic on lower third (called after base render)"""
    try:
        import os
        church_path = 'attached_assets/Trin_High_Qual_-_trans_1766487556493.png'
        if not os.path.exists(church_path):
            return
        
        church_img = Image.open(church_path).convert('RGBA')
        
        bar_height = background_end - lower_third_start
        target_height = int(bar_height * 1.2)
        aspect_ratio = church_img.width / church_img.height
        target_width = int(target_height * aspect_ratio)
        
        church_resized = church_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        alpha = church_resized.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.35))
        church_resized.putalpha(alpha)
        
        x_pos = width - target_width - 50
        y_pos = lower_third_start - int(target_height * 0.15)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        temp_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        temp_layer.paste(church_resized, (x_pos, y_pos), church_resized)
        
        img.alpha_composite(temp_layer)
        
    except Exception as e:
        print(f"Could not overlay church image: {e}")


# =============================================================================
# BLANK LOWER THIRD STYLE RENDERER FUNCTIONS
# =============================================================================

def _render_blank_lower_third_classic(draw: ImageDraw.Draw, width: int, height: int, 
                                       lower_third_start: int, background_end: int, 
                                       liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Classic style blank template - same visual design as classic but without text"""
    _render_lower_third_classic(draw, width, height, lower_third_start, background_end, liturgical_colors)


def _render_blank_lower_third_minimal(draw: ImageDraw.Draw, width: int, height: int, 
                                       lower_third_start: int, background_end: int, 
                                       liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Minimal style blank template"""
    _render_lower_third_minimal(draw, width, height, lower_third_start, background_end, liturgical_colors)


def _render_blank_lower_third_modern_glass(draw: ImageDraw.Draw, width: int, height: int, 
                                            lower_third_start: int, background_end: int, 
                                            liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Modern Glass style blank template"""
    _render_lower_third_modern_glass(draw, width, height, lower_third_start, background_end, liturgical_colors)


def _render_blank_lower_third_bold_banner(draw: ImageDraw.Draw, width: int, height: int, 
                                           lower_third_start: int, background_end: int, 
                                           liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Bold Banner style blank template"""
    _render_lower_third_bold_banner(draw, width, height, lower_third_start, background_end, liturgical_colors)


def _render_blank_lower_third_elegant(draw: ImageDraw.Draw, width: int, height: int, 
                                       lower_third_start: int, background_end: int, 
                                       liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Elegant style blank template"""
    _render_lower_third_elegant(draw, width, height, lower_third_start, background_end, liturgical_colors)


def _render_blank_lower_third_christmas_trinity(draw: ImageDraw.Draw, width: int, height: int, 
                                                 lower_third_start: int, background_end: int, 
                                                 liturgical_colors: Dict[str, Tuple[int, int, int, int]]) -> None:
    """Christmas Trinity style blank template"""
    _render_lower_third_christmas_trinity(draw, width, height, lower_third_start, background_end, liturgical_colors)


# =============================================================================
# STYLE REGISTRIES
# =============================================================================

LOWER_THIRD_STYLE_REGISTRY: Dict[str, callable] = {
    'classic': _render_lower_third_classic,
    'minimal': _render_lower_third_minimal,
    'modern_glass': _render_lower_third_modern_glass,
    'bold_banner': _render_lower_third_bold_banner,
    'elegant': _render_lower_third_elegant,
    'christmas_trinity': _render_lower_third_christmas_trinity,
}

BLANK_LOWER_THIRD_STYLE_REGISTRY: Dict[str, callable] = {
    'classic': _render_blank_lower_third_classic,
    'minimal': _render_blank_lower_third_minimal,
    'modern_glass': _render_blank_lower_third_modern_glass,
    'bold_banner': _render_blank_lower_third_bold_banner,
    'elegant': _render_blank_lower_third_elegant,
    'christmas_trinity': _render_blank_lower_third_christmas_trinity,
}


def _create_christmas_trinity_title_card(liturgical_reference: str, width: int, height: int, branding: Dict[str, Any]) -> Image.Image:
    """Create a special Christmas-themed title card with Trinity Church branding
    
    Features rich gold and burgundy colors, Trinity Church building graphic,
    and festive Christmas liturgical design.
    """
    import math
    
    gold_primary = (212, 175, 55)
    gold_light = (245, 212, 100)
    gold_dark = (160, 130, 40)
    burgundy = (128, 0, 32)
    burgundy_dark = (80, 0, 20)
    cream = (255, 248, 235)
    
    img = Image.new('RGBA', (width, height), color=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 255))
    draw = ImageDraw.Draw(img)
    
    gradient_steps = 60
    for i in range(gradient_steps):
        y_pos = int((height * i) / gradient_steps)
        next_y = int((height * (i + 1)) / gradient_steps)
        
        factor = i / gradient_steps
        r = int(burgundy_dark[0] + (burgundy[0] - burgundy_dark[0]) * factor * 0.7)
        g = int(burgundy_dark[1] + (burgundy[1] - burgundy_dark[1]) * factor * 0.5)
        b = int(burgundy_dark[2] + (burgundy[2] - burgundy_dark[2]) * factor * 0.7)
        
        draw.rectangle([0, y_pos, width, next_y], fill=(r, g, b, 255))
    
    border_width = 40
    draw.rectangle([border_width, border_width, width - border_width, height - border_width], 
                   outline=(gold_primary[0], gold_primary[1], gold_primary[2], 255), width=10)
    draw.rectangle([border_width + 15, border_width + 15, width - border_width - 15, height - border_width - 15], 
                   outline=(gold_light[0], gold_light[1], gold_light[2], 180), width=3)
    
    corner_size = 100
    corner_inset = border_width + 30
    corner_positions = [
        (corner_inset, corner_inset, 180, 270),
        (width - corner_inset - corner_size, corner_inset, 270, 360),
        (corner_inset, height - corner_inset - corner_size, 90, 180),
        (width - corner_inset - corner_size, height - corner_inset - corner_size, 0, 90)
    ]
    
    for x, y, start, end in corner_positions:
        draw.arc([x, y, x + corner_size, y + corner_size], start=start, end=end, 
                 fill=(gold_light[0], gold_light[1], gold_light[2], 255), width=8)
    
    center_x = width // 2
    
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        for r in [30, 50]:
            end_x = center_x + int(r * math.cos(rad))
            end_y = 160 + int(r * math.sin(rad))
            draw.line([(center_x, 160), (end_x, end_y)], 
                      fill=(gold_light[0], gold_light[1], gold_light[2], 255), width=3)
    draw.ellipse([center_x - 15, 160 - 15, center_x + 15, 160 + 15],
                 fill=(gold_light[0], gold_light[1], gold_light[2], 255))
    draw.ellipse([center_x - 8, 160 - 8, center_x + 8, 160 + 8],
                 fill=(cream[0], cream[1], cream[2], 255))
    
    try:
        church_path = 'attached_assets/Trin_overhead_2008_1766580299806.png'
        import os
        if os.path.exists(church_path):
            church_img = Image.open(church_path).convert('RGBA')
            
            target_height = int(height * 0.6)
            aspect_ratio = church_img.width / church_img.height
            target_width = int(target_height * aspect_ratio)
            
            church_resized = church_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            alpha = church_resized.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.35))
            church_resized.putalpha(alpha)
            
            x_pos = width - target_width - 80
            y_pos = (height - target_height) // 2
            
            temp_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            temp_layer.paste(church_resized, (x_pos, y_pos), church_resized)
            img.alpha_composite(temp_layer)
            
            draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"Could not load church image for Christmas title card: {e}")
    
    title_font = load_stack_sans_font(70, bold=True)
    subtitle_font = load_stack_sans_font(55, bold=True)
    church_font = load_stack_sans_font(60, bold=True)
    
    reference_parts = liturgical_reference.split('\n')
    service_type = reference_parts[0] if reference_parts else "Christmas Eve"
    service_date = reference_parts[1] if len(reference_parts) > 1 else ""
    
    bbox = draw.textbbox((0, 0), service_type, font=title_font)
    service_width = bbox[2] - bbox[0]
    service_x = (width - service_width) // 2
    service_y = 250
    
    outline_width = 5
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((service_x + offset_x, service_y + offset_y), service_type, 
                          fill=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 255), font=title_font)
    draw.text((service_x, service_y), service_type, fill=(cream[0], cream[1], cream[2], 255), font=title_font)
    
    if service_date:
        date_bbox = draw.textbbox((0, 0), service_date, font=subtitle_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (width - date_width) // 2
        date_y = 340
        
        outline_width = 4
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((date_x + offset_x, date_y + offset_y), service_date, 
                              fill=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 255), font=subtitle_font)
        draw.text((date_x, date_y), service_date, 
                  fill=(gold_light[0], gold_light[1], gold_light[2], 255), font=subtitle_font)
    
    try:
        logo_path = "attached_assets/Trin_overhead_2008_1766580299806.png"
        import os
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert('RGBA')
            
            max_logo_width = 500
            max_logo_height = 400
            
            width_ratio = max_logo_width / logo.width
            height_ratio = max_logo_height / logo.height
            scale_ratio = min(width_ratio, height_ratio)
            
            new_logo_width = int(logo.width * scale_ratio)
            new_logo_height = int(logo.height * scale_ratio)
            
            logo_resized = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
            
            logo_x = (width - new_logo_width) // 2
            logo_y = 450
            
            img.paste(logo_resized, (logo_x, logo_y), logo_resized)
            draw = ImageDraw.Draw(img)
    except Exception as e:
        print(f"Could not load logo for Christmas title card: {e}")
    
    divider_y = height - 70
    for i in range(3):
        offset = i * 12
        draw.line([(center_x - 350 - offset, divider_y + i * 2), (center_x - 80, divider_y + i * 2)], 
                  fill=(gold_primary[0], gold_primary[1], gold_primary[2], 200), width=2)
        draw.line([(center_x + 80, divider_y + i * 2), (center_x + 350 + offset, divider_y + i * 2)], 
                  fill=(gold_primary[0], gold_primary[1], gold_primary[2], 200), width=2)
    
    diamond_size = 20
    draw.polygon([
        (center_x, divider_y - diamond_size),
        (center_x + diamond_size, divider_y),
        (center_x, divider_y + diamond_size),
        (center_x - diamond_size, divider_y)
    ], fill=(gold_light[0], gold_light[1], gold_light[2], 255))
    
    church_name = branding.get('church_name', 'Trinity Episcopal Church')
    church_bbox = draw.textbbox((0, 0), church_name, font=church_font)
    church_width = church_bbox[2] - church_bbox[0]
    church_x = (width - church_width) // 2
    church_y = height - 150
    
    outline_width = 4
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((church_x + offset_x, church_y + offset_y), church_name, 
                          fill=(burgundy_dark[0], burgundy_dark[1], burgundy_dark[2], 255), font=church_font)
    draw.text((church_x, church_y), church_name, 
              fill=(gold_light[0], gold_light[1], gold_light[2], 255), font=church_font)
    
    return img


def create_title_card(liturgical_reference: str, date_str: Optional[str] = None, width: int = 1920, height: int = 1080, is_funeral: bool = False, liturgical_season: Optional[str] = None, theme: str = 'liturgical', branding: Optional[Dict[str, Any]] = None, style: str = 'classic') -> Image.Image:
    """Create a full-screen title card with liturgical reference and church name
    
    Args:
        liturgical_reference: The liturgical reference text to display
        date_str: Date string for liturgical season detection (ignored if liturgical_season is provided)
        width: Image width in pixels
        height: Image height in pixels
        is_funeral: If True, use black background with white text instead of theme colors
        liturgical_season: Directly specify liturgical season (advent, christmas, lent, etc.)
        theme: Theme name ('liturgical' or 'concert'), defaults to 'liturgical'
        branding: Optional branding configuration dictionary
        style: Visual style name (e.g., 'christmas_trinity' for special Christmas branding)
    """
    if branding is None:
        branding = load_branding_config()
    
    if style.lower() == 'christmas_trinity' and not is_funeral:
        return _create_christmas_trinity_title_card(liturgical_reference, width, height, branding)
    
    # Create image with appropriate background based on service type and theme
    if is_funeral:
        # Funeral: black background
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 255))
    elif theme == 'concert':
        # Concert: grey background with 0.85 opacity (alpha 217 = 0.85 * 255)
        img = Image.new('RGBA', (width, height), color=(128, 128, 128, 217))
    else:
        # Regular liturgical: white background and 50% opacity (alpha 128 = 50%)
        img = Image.new('RGBA', (width, height), color=(255, 255, 255, 128))
    
    draw = ImageDraw.Draw(img)
    
    # Determine theme colors or use funeral colors
    if is_funeral:
        # Funeral: white text on black background
        liturgical_colors = {
            'background': (0, 0, 0, 255),        # Black
            'accent': (255, 255, 255, 255),      # White
            'title': (255, 255, 255, 255),       # White
            'text': (255, 255, 255, 255)         # White
        }
    else:
        # Use theme system
        liturgical_colors = get_theme(theme, date_str=date_str, liturgical_season=liturgical_season)
    
    # Load Stack Sans fonts for title card
    title_font = load_stack_sans_font(65, bold=True)
    church_font = load_stack_sans_font(70, bold=True)
    decorative_font = load_stack_sans_font(35, bold=False)
    print(f"✅ Successfully loaded Stack Sans fonts: title=65pt, church=70pt")
    
    # Draw decorative border with liturgical accent color
    border_width = 30
    draw.rectangle([border_width, border_width, width - border_width, height - border_width], 
                   outline=liturgical_colors['accent'], width=8)
    
    # Draw decorative corner flourishes
    corner_size = 120
    corner_color = liturgical_colors['accent']
    
    # Top-left corner
    draw.arc([border_width + 20, border_width + 20, border_width + corner_size, border_width + corner_size], 
             start=180, end=270, fill=corner_color, width=6)
    
    # Top-right corner
    draw.arc([width - border_width - corner_size, border_width + 20, width - border_width - 20, border_width + corner_size], 
             start=270, end=0, fill=corner_color, width=6)
    
    # Bottom-left corner
    draw.arc([border_width + 20, height - border_width - corner_size, border_width + corner_size, height - border_width - 20], 
             start=90, end=180, fill=corner_color, width=6)
    
    # Bottom-right corner
    draw.arc([width - border_width - corner_size, height - border_width - corner_size, width - border_width - 20, height - border_width - 20], 
             start=0, end=90, fill=corner_color, width=6)
    
    # Draw decorative horizontal dividers with gradient effect
    divider_y_top = 220
    divider_y_bottom = height - 220
    center_x = width // 2
    
    # Top divider - decorative lines emanating from center
    for i in range(3):
        offset = i * 15
        draw.line([(center_x - 400 - offset, divider_y_top + i * 3), (center_x - 50, divider_y_top + i * 3)], 
                  fill=liturgical_colors['accent'], width=2)
        draw.line([(center_x + 50, divider_y_top + i * 3), (center_x + 400 + offset, divider_y_top + i * 3)], 
                  fill=liturgical_colors['accent'], width=2)
    
    # Bottom divider
    for i in range(3):
        offset = i * 15
        draw.line([(center_x - 400 - offset, divider_y_bottom + i * 3), (center_x - 50, divider_y_bottom + i * 3)], 
                  fill=liturgical_colors['accent'], width=2)
        draw.line([(center_x + 50, divider_y_bottom + i * 3), (center_x + 400 + offset, divider_y_bottom + i * 3)], 
                  fill=liturgical_colors['accent'], width=2)
    
    # Draw decorative center ornament (diamond shape)
    diamond_size = 25
    draw.polygon([
        (center_x, divider_y_top - diamond_size),
        (center_x + diamond_size, divider_y_top),
        (center_x, divider_y_top + diamond_size),
        (center_x - diamond_size, divider_y_top)
    ], fill=liturgical_colors['accent'])
    
    draw.polygon([
        (center_x, divider_y_bottom - diamond_size),
        (center_x + diamond_size, divider_y_bottom),
        (center_x, divider_y_bottom + diamond_size),
        (center_x - diamond_size, divider_y_bottom)
    ], fill=liturgical_colors['accent'])
    
    # Add church logo in the center
    try:
        logo_path = "attached_assets/Trin High Qual - trans_1760427955140.png"
        logo = Image.open(logo_path)
        
        # Scale logo to fit nicely in the center area (max 500px width)
        max_logo_width = 500
        max_logo_height = 400
        
        # Calculate scaling to fit within both constraints
        width_ratio = max_logo_width / logo.width
        height_ratio = max_logo_height / logo.height
        scale_ratio = min(width_ratio, height_ratio)
        
        new_logo_width = int(logo.width * scale_ratio)
        new_logo_height = int(logo.height * scale_ratio)
        
        logo_resized = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
        
        # Convert to RGBA if needed
        if logo_resized.mode != 'RGBA':
            logo_resized = logo_resized.convert('RGBA')
        
        # Position logo in the center of the card
        logo_x = (width - new_logo_width) // 2
        logo_y = (height - new_logo_height) // 2
        
        # Paste logo onto the card
        img.paste(logo_resized, (logo_x, logo_y), logo_resized)
    except Exception as e:
        print(f"Could not load church logo for title card: {e}")
    
    # Split liturgical reference into service type and date (separated by newline)
    reference_parts = liturgical_reference.split('\n')
    service_type = reference_parts[0] if reference_parts else "Holy Eucharist"
    service_date = reference_parts[1] if len(reference_parts) > 1 else ""
    
    # Draw "Holy Eucharist" ABOVE the first separator
    bbox = draw.textbbox((0, 0), service_type, font=title_font)
    service_width = bbox[2] - bbox[0]
    service_x = (width - service_width) // 2
    service_y = 100  # Above the first divider at y=220
    
    # Black outline (draw text in 8 directions)
    outline_width = 4
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((service_x + offset_x, service_y + offset_y), service_type, fill=(0, 0, 0, 255), font=title_font)
    
    # Main text
    draw.text((service_x, service_y), service_type, fill=liturgical_colors['title'], font=title_font)
    
    # Draw date JUST BELOW the first separator
    if service_date:
        date_bbox = draw.textbbox((0, 0), service_date, font=church_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (width - date_width) // 2
        date_y = 250  # Just below the first divider at y=220
        
        # Black outline (draw text in 8 directions)
        outline_width = 3
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((date_x + offset_x, date_y + offset_y), service_date, fill=(0, 0, 0, 255), font=church_font)
        
        # Main text
        draw.text((date_x, date_y), service_date, fill=liturgical_colors['text'], font=church_font)
    
    # Draw church name BELOW the second separator
    church_name = branding.get('church_name', 'Trinity Episcopal Church')
    church_bbox = draw.textbbox((0, 0), church_name, font=church_font)
    church_width = church_bbox[2] - church_bbox[0]
    church_x = (width - church_width) // 2
    church_y = height - 170  # Below the second divider at y=(height-220)=860
    
    # Black outline (draw text in 8 directions)
    outline_width = 3
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((church_x + offset_x, church_y + offset_y), church_name, fill=(0, 0, 0, 255), font=church_font)
    
    # Main text
    draw.text((church_x, church_y), church_name, fill=liturgical_colors['text'], font=church_font)
    
    logo_path = branding.get('logo_path') if branding else None
    img = overlay_logo(img, logo_path, position='top-right', max_width=220)
    
    return img

def create_announcement_slide(announcement_data: dict, width: int = 1920, height: int = 1080, branding: Optional[Dict[str, Any]] = None, style: str = 'classic') -> Image.Image:
    """Create an announcement slide with type-specific formatting
    
    Args:
        announcement_data: Dictionary containing:
            - type: 'event', 'prayer', 'giving', or 'general'
            - title: Announcement title
            - fields: Dict with type-specific fields
            - liturgicalSeason: Optional season for colors
            - isMemorial: Boolean for memorial theme
        width: Image width in pixels
        height: Image height in pixels
        branding: Optional branding configuration dictionary
        style: Visual style name (e.g., 'christmas_trinity' for special Christmas branding)
    
    Returns:
        PIL Image object
    """
    if branding is None:
        branding = load_branding_config()
    
    ann_type = announcement_data.get('type', 'general')
    title = announcement_data.get('title', '')
    fields = announcement_data.get('fields', {})
    liturgical_season = announcement_data.get('liturgicalSeason')
    is_memorial = announcement_data.get('isMemorial', False)
    
    # Check for Christmas Trinity style
    is_christmas_trinity = (style == 'christmas_trinity')
    
    if is_christmas_trinity:
        # Christmas Trinity color palette
        gold = (212, 175, 55, 255)
        gold_light = (255, 215, 100, 255)
        burgundy = (128, 0, 32, 255)
        cream = (255, 248, 235, 255)
        
        # Create burgundy gradient background
        img = Image.new('RGBA', (width, height), color=burgundy[:3] + (255,))
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        for i in range(height):
            blend = i / height
            r = int(burgundy[0] * (1 - blend * 0.3) + 80 * blend * 0.3)
            g = int(burgundy[1] * (1 - blend * 0.3))
            b = int(burgundy[2] * (1 - blend * 0.3) + 40 * blend * 0.3)
            draw_overlay.rectangle([(0, i), (width, i + 1)], fill=(r, g, b, 255))
        
        img = Image.alpha_composite(img, overlay)
        
        # Add church building overlay
        try:
            church_img = Image.open('attached_assets/Trin_High_Qual_-_trans_1766487556493.png').convert('RGBA')
            church_size = int(min(width, height) * 0.5)
            church_img = church_img.resize((church_size, church_size), Image.LANCZOS)
            
            church_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            church_x = width - church_size + 100
            church_y = (height - church_size) // 2
            
            alpha = church_img.split()[3]
            alpha = alpha.point(lambda x: int(x * 0.15))
            church_img.putalpha(alpha)
            
            church_overlay.paste(church_img, (church_x, church_y), church_img)
            img = Image.alpha_composite(img, church_overlay)
        except Exception as e:
            print(f"Could not load church image for announcement: {e}")
        
        theme_colors = {
            'background': burgundy,
            'accent': gold,
            'title': cream,
            'text': cream
        }
    elif is_memorial:
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 255))
        theme_colors = {
            'background': (0, 0, 0, 255),
            'accent': (255, 255, 255, 255),
            'title': (255, 255, 255, 255),
            'text': (255, 255, 255, 255)
        }
    else:
        theme_colors = get_theme('liturgical', liturgical_season=liturgical_season)
        r, g, b, a = theme_colors['background']
        img = Image.new('RGBA', (width, height), color=(r, g, b, 255))
    
    draw = ImageDraw.Draw(img)
    
    # Load Stack Sans fonts for announcement slides
    title_font = load_stack_sans_font(80, bold=True)
    subtitle_font = load_stack_sans_font(50, bold=True)
    field_label_font = load_stack_sans_font(40, bold=True)
    field_text_font = load_stack_sans_font(38, bold=False)
    
    type_icons = {
        'event': '📅',
        'prayer': '🙏',
        'giving': '💝',
        'general': '📢'
    }
    type_labels = {
        'event': 'Event',
        'prayer': 'Prayer Request',
        'giving': 'Giving',
        'general': 'Announcement'
    }
    
    icon = type_icons.get(ann_type, '📢')
    type_label = type_labels.get(ann_type, 'Announcement')
    
    card_width = 1400
    card_height = 800
    card_x = (width - card_width) // 2
    card_y = (height - card_height) // 2
    
    if is_christmas_trinity:
        card_bg = (255, 248, 235, 240)  # Cream card
        text_color = (80, 0, 20, 255)  # Dark burgundy text
    elif is_memorial:
        card_bg = (40, 40, 40, 230)
        text_color = (255, 255, 255, 255)
    else:
        card_bg = (255, 255, 255, 240)
        text_color = (0, 0, 0, 255)
    
    draw.rectangle([card_x, card_y, card_x + card_width, card_y + card_height], 
                   fill=card_bg, outline=theme_colors['accent'], width=6)
    
    current_y = card_y + 50
    
    type_header = f"{icon} {type_label}"
    type_bbox = draw.textbbox((0, 0), type_header, font=subtitle_font)
    type_width = type_bbox[2] - type_bbox[0]
    type_x = (width - type_width) // 2
    draw.text((type_x, current_y), type_header, fill=theme_colors['accent'], font=subtitle_font)
    current_y += 80
    
    title_lines = []
    words = title.split()
    current_line = []
    max_title_width = card_width - 100
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_bbox = draw.textbbox((0, 0), test_line, font=title_font)
        if test_bbox[2] - test_bbox[0] > max_title_width and current_line:
            title_lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        title_lines.append(' '.join(current_line))
    
    for line in title_lines:
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, current_y), line, fill=text_color, font=title_font)
        current_y += 90
    
    current_y += 20
    
    draw.line([(card_x + 100, current_y), (card_x + card_width - 100, current_y)], 
              fill=theme_colors['accent'], width=3)
    current_y += 40
    
    max_text_width = card_width - 200
    
    if ann_type == 'event':
        if fields.get('date'):
            label = "Date: "
            value = fields['date']
            draw.text((card_x + 100, current_y), label, fill=theme_colors['accent'], font=field_label_font)
            label_bbox = draw.textbbox((0, 0), label, font=field_label_font)
            label_width = label_bbox[2] - label_bbox[0]
            draw.text((card_x + 100 + label_width, current_y), value, fill=text_color, font=field_text_font)
            current_y += 50
        
        if fields.get('time'):
            label = "Time: "
            value = fields['time']
            draw.text((card_x + 100, current_y), label, fill=theme_colors['accent'], font=field_label_font)
            label_bbox = draw.textbbox((0, 0), label, font=field_label_font)
            label_width = label_bbox[2] - label_bbox[0]
            draw.text((card_x + 100 + label_width, current_y), value, fill=text_color, font=field_text_font)
            current_y += 50
        
        if fields.get('location'):
            label = "Location: "
            value = fields['location']
            draw.text((card_x + 100, current_y), label, fill=theme_colors['accent'], font=field_label_font)
            label_bbox = draw.textbbox((0, 0), label, font=field_label_font)
            label_width = label_bbox[2] - label_bbox[0]
            draw.text((card_x + 100 + label_width, current_y), value, fill=text_color, font=field_text_font)
            current_y += 50
        
        if fields.get('description'):
            current_y += 10
            desc_lines = textwrap.wrap(fields['description'], width=60)
            for line in desc_lines[:3]:
                draw.text((card_x + 100, current_y), line, fill=text_color, font=field_text_font)
                current_y += 45
    
    elif ann_type == 'prayer':
        if fields.get('intention'):
            intention_lines = textwrap.wrap(fields['intention'], width=65)
            for line in intention_lines[:6]:
                draw.text((card_x + 100, current_y), line, fill=text_color, font=field_text_font)
                current_y += 45
    
    elif ann_type == 'giving':
        if fields.get('goal'):
            draw.text((card_x + 100, current_y), fields['goal'], fill=theme_colors['accent'], font=subtitle_font)
            current_y += 60
        
        if fields.get('description'):
            desc_lines = textwrap.wrap(fields['description'], width=65)
            for line in desc_lines[:5]:
                draw.text((card_x + 100, current_y), line, fill=text_color, font=field_text_font)
                current_y += 45
    
    elif ann_type == 'general':
        if fields.get('subtitle'):
            subtitle_bbox = draw.textbbox((0, 0), fields['subtitle'], font=field_label_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (width - subtitle_width) // 2
            draw.text((subtitle_x, current_y), fields['subtitle'], fill=theme_colors['accent'], font=field_label_font)
            current_y += 55
        
        if fields.get('description'):
            desc_lines = textwrap.wrap(fields['description'], width=65)
            for line in desc_lines[:6]:
                draw.text((card_x + 100, current_y), line, fill=text_color, font=field_text_font)
                current_y += 45
    
    corner_size = 40
    corner_color = theme_colors['accent']
    draw.arc([card_x + 10, card_y + 10, card_x + corner_size, card_y + corner_size], 
             start=180, end=270, fill=corner_color, width=4)
    draw.arc([card_x + card_width - corner_size, card_y + 10, 
              card_x + card_width - 10, card_y + corner_size], 
             start=270, end=0, fill=corner_color, width=4)
    draw.arc([card_x + 10, card_y + card_height - corner_size, 
              card_x + corner_size, card_y + card_height - 10], 
             start=90, end=180, fill=corner_color, width=4)
    draw.arc([card_x + card_width - corner_size, card_y + card_height - corner_size, 
              card_x + card_width - 10, card_y + card_height - 10], 
             start=0, end=90, fill=corner_color, width=4)
    
    logo_path = branding.get('logo_path') if branding else None
    img = overlay_logo(img, logo_path, position='top-right', max_width=220)
    
    return img

def create_service_order_slide(order_item: str, liturgical_season: Optional[str] = None, is_memorial: bool = False, show_number: bool = False, item_number: int = 1, width: int = 1920, height: int = 1080, branding: Optional[Dict[str, Any]] = None) -> Image.Image:
    """
    Create a service order slide showing one service element
    
    Args:
        order_item: Text for this service element (e.g., "Opening Hymn")
        liturgical_season: Season for theming
        is_memorial: Use black/white memorial theme
        show_number: Include item number on slide
        item_number: The number to display if show_number is True
        width: Image width in pixels
        height: Image height in pixels
        branding: Optional branding configuration dictionary
    
    Returns:
        PIL Image object
    """
    if branding is None:
        branding = load_branding_config()
    
    if is_memorial:
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 255))
        theme_colors = {
            'background': (0, 0, 0, 255),
            'accent': (200, 200, 200, 255),
            'title': (255, 255, 255, 255),
            'text': (255, 255, 255, 255)
        }
    else:
        theme_colors = get_theme('liturgical', liturgical_season=liturgical_season)
        r, g, b, a = theme_colors['background']
        img = Image.new('RGBA', (width, height), color=(r, g, b, 255))
        
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        accent_r, accent_g, accent_b, accent_a = theme_colors['accent']
        gradient_height = height // 3
        for i in range(gradient_height):
            alpha = int(100 * (1 - i / gradient_height))
            draw_overlay.rectangle(
                [(0, i), (width, i + 1)],
                fill=(accent_r, accent_g, accent_b, alpha)
            )
        
        img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)
    
    # Load Stack Sans fonts for service order slides
    main_font = load_stack_sans_font(90, bold=True)
    number_font = load_stack_sans_font(140, bold=True)
    
    if show_number:
        number_text = str(item_number)
        number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
        number_width = number_bbox[2] - number_bbox[0]
        number_height = number_bbox[3] - number_bbox[1]
        number_x = 80
        number_y = 80
        
        outline_width = 4
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((number_x + offset_x, number_y + offset_y), number_text, fill=(0, 0, 0, 200), font=number_font)
        
        draw.text((number_x, number_y), number_text, fill=theme_colors['accent'], font=number_font)
    
    words = order_item.split()
    lines = []
    current_line = []
    max_width = width - 200
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_bbox = draw.textbbox((0, 0), test_line, font=main_font)
        if test_bbox[2] - test_bbox[0] > max_width and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(' '.join(current_line))
    
    total_height = len(lines) * 110
    start_y = (height - total_height) // 2
    
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=main_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        line_y = start_y + (i * 110)
        
        outline_width = 4
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((line_x + offset_x, line_y + offset_y), line, fill=(0, 0, 0, 200), font=main_font)
        
        draw.text((line_x, line_y), line, fill=theme_colors['title'], font=main_font)
    
    if not is_memorial:
        corner_size = 60
        corner_color = theme_colors['accent']
        draw.ellipse([50, 50, 50 + corner_size, 50 + corner_size], outline=corner_color, width=5)
        draw.ellipse([width - 50 - corner_size, 50, width - 50, 50 + corner_size], outline=corner_color, width=5)
        draw.ellipse([50, height - 50 - corner_size, 50 + corner_size, height - 50], outline=corner_color, width=5)
        draw.ellipse([width - 50 - corner_size, height - 50 - corner_size, width - 50, height - 50], outline=corner_color, width=5)
    
    logo_path = branding.get('logo_path') if branding else None
    img = overlay_logo(img, logo_path, position='top-right', max_width=220)
    
    return img

def create_countdown_slide(minutes: int, liturgical_season: Optional[str] = None, is_memorial: bool = False, welcome_message: Optional[str] = None, service_time: Optional[str] = None, width: int = 1920, height: int = 1080, branding: Optional[Dict[str, Any]] = None, style: str = 'classic') -> Image.Image:
    """
    Create countdown timer slide
    
    Args:
        minutes: Number of minutes to display (e.g., 15)
        liturgical_season: Season for theming
        is_memorial: Use black/white memorial theme
        welcome_message: Optional welcome text
        service_time: Optional service start time (e.g., "10:00 AM")
        width: Image width in pixels
        height: Image height in pixels
        branding: Optional branding configuration dictionary
        style: Visual style name (e.g., 'christmas_trinity' for special Christmas branding)
    
    Returns:
        PIL Image object
    """
    if branding is None:
        branding = load_branding_config()
    
    # Check for Christmas Trinity style
    is_christmas_trinity = (style == 'christmas_trinity')
    
    if is_christmas_trinity:
        # Christmas Trinity color palette
        gold = (212, 175, 55, 255)
        burgundy = (128, 0, 32, 255)
        cream = (255, 248, 235, 255)
        
        # Create burgundy gradient background
        img = Image.new('RGBA', (width, height), color=burgundy[:3] + (255,))
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        # Vertical gradient from darker burgundy at top to lighter at bottom
        for i in range(height):
            blend = i / height
            r = int(burgundy[0] * (1 - blend * 0.3) + 80 * blend * 0.3)
            g = int(burgundy[1] * (1 - blend * 0.3))
            b = int(burgundy[2] * (1 - blend * 0.3) + 40 * blend * 0.3)
            draw_overlay.rectangle([(0, i), (width, i + 1)], fill=(r, g, b, 255))
        
        img = Image.alpha_composite(img, overlay)
        
        # Add church building overlay
        try:
            church_img = Image.open('attached_assets/Trin_High_Qual_-_trans_1766487556493.png').convert('RGBA')
            church_size = int(min(width, height) * 0.7)
            church_img = church_img.resize((church_size, church_size), Image.LANCZOS)
            
            # Apply gold tint and reduce opacity
            church_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            church_x = (width - church_size) // 2
            church_y = (height - church_size) // 2
            
            # Reduce opacity to 25%
            alpha = church_img.split()[3]
            alpha = alpha.point(lambda x: int(x * 0.25))
            church_img.putalpha(alpha)
            
            church_overlay.paste(church_img, (church_x, church_y), church_img)
            img = Image.alpha_composite(img, church_overlay)
        except Exception as e:
            print(f"Could not load church image for countdown: {e}")
        
        theme_colors = {
            'background': burgundy,
            'accent': gold,
            'title': cream,
            'text': cream
        }
    elif is_memorial:
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 255))
        theme_colors = {
            'background': (0, 0, 0, 255),
            'accent': (200, 200, 200, 255),
            'title': (255, 255, 255, 255),
            'text': (255, 255, 255, 255)
        }
    else:
        theme_colors = get_theme('liturgical', liturgical_season=liturgical_season)
        r, g, b, a = theme_colors['background']
        img = Image.new('RGBA', (width, height), color=(r, g, b, 255))
        
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        accent_r, accent_g, accent_b, accent_a = theme_colors['accent']
        gradient_height = height // 2
        for i in range(gradient_height):
            alpha = int(120 * (1 - i / gradient_height))
            draw_overlay.rectangle(
                [(0, height // 2 - gradient_height // 2 + i), (width, height // 2 - gradient_height // 2 + i + 1)],
                fill=(accent_r, accent_g, accent_b, alpha)
            )
        
        img = Image.alpha_composite(img, overlay)
    
    draw = ImageDraw.Draw(img)
    
    # Load Stack Sans fonts for countdown timer
    header_font = load_stack_sans_font(60, bold=True)
    countdown_font = load_stack_sans_font(180, bold=True)
    minutes_font = load_stack_sans_font(60, bold=True)
    info_font = load_stack_sans_font(45, bold=False)
    welcome_font = load_stack_sans_font(40, bold=False)
    
    if not is_memorial:
        center_x = width // 2
        center_y = height // 2
        radius = 250
        
        if is_christmas_trinity:
            # Christmas Trinity: Gold circle with decorative stars
            gold = (212, 175, 55, 255)
            
            # Draw outer decorative ring
            draw.ellipse(
                [center_x - radius - 10, center_y - radius - 10, center_x + radius + 10, center_y + radius + 10],
                outline=gold,
                width=3
            )
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                outline=gold,
                width=8
            )
            
            # Draw Christmas stars around the circle
            import math
            star_positions = [0, 45, 90, 135, 180, 225, 270, 315]
            for angle in star_positions:
                star_x = center_x + int((radius + 40) * math.cos(math.radians(angle - 90)))
                star_y = center_y + int((radius + 40) * math.sin(math.radians(angle - 90)))
                star_size = 12
                # Draw 4-point star
                draw.polygon([
                    (star_x, star_y - star_size),
                    (star_x + star_size // 3, star_y - star_size // 3),
                    (star_x + star_size, star_y),
                    (star_x + star_size // 3, star_y + star_size // 3),
                    (star_x, star_y + star_size),
                    (star_x - star_size // 3, star_y + star_size // 3),
                    (star_x - star_size, star_y),
                    (star_x - star_size // 3, star_y - star_size // 3),
                ], fill=gold)
            
            # Draw tick marks
            for angle in range(0, 360, 30):
                x1 = center_x + int((radius - 20) * math.cos(math.radians(angle)))
                y1 = center_y + int((radius - 20) * math.sin(math.radians(angle)))
                x2 = center_x + int(radius * math.cos(math.radians(angle)))
                y2 = center_y + int(radius * math.sin(math.radians(angle)))
                draw.line([(x1, y1), (x2, y2)], fill=gold, width=4)
        else:
            # Standard liturgical timer circle
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                outline=theme_colors['accent'],
                width=8
            )
            for angle in range(0, 360, 30):
                import math
                x1 = center_x + int((radius - 20) * math.cos(math.radians(angle)))
                y1 = center_y + int((radius - 20) * math.sin(math.radians(angle)))
                x2 = center_x + int(radius * math.cos(math.radians(angle)))
                y2 = center_y + int(radius * math.sin(math.radians(angle)))
                draw.line([(x1, y1), (x2, y2)], fill=theme_colors['accent'], width=4)
    
    header_text = "Service Begins In"
    header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
    header_width = header_bbox[2] - header_bbox[0]
    header_x = (width - header_width) // 2
    header_y = 200
    
    outline_width = 3
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((header_x + offset_x, header_y + offset_y), header_text, fill=(0, 0, 0, 200), font=header_font)
    
    draw.text((header_x, header_y), header_text, fill=theme_colors['title'], font=header_font)
    
    countdown_text = str(minutes)
    countdown_bbox = draw.textbbox((0, 0), countdown_text, font=countdown_font)
    countdown_width = countdown_bbox[2] - countdown_bbox[0]
    countdown_height = countdown_bbox[3] - countdown_bbox[1]
    countdown_x = (width - countdown_width) // 2
    countdown_y = (height - countdown_height) // 2 - 30
    
    outline_width = 5
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((countdown_x + offset_x, countdown_y + offset_y), countdown_text, fill=(0, 0, 0, 200), font=countdown_font)
    
    draw.text((countdown_x, countdown_y), countdown_text, fill=theme_colors['title'], font=countdown_font)
    
    minutes_text = "Minute" if minutes == 1 else "Minutes"
    minutes_bbox = draw.textbbox((0, 0), minutes_text, font=minutes_font)
    minutes_width = minutes_bbox[2] - minutes_bbox[0]
    minutes_x = (width - minutes_width) // 2
    minutes_y = countdown_y + countdown_height + 20
    
    outline_width = 3
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((minutes_x + offset_x, minutes_y + offset_y), minutes_text, fill=(0, 0, 0, 200), font=minutes_font)
    
    draw.text((minutes_x, minutes_y), minutes_text, fill=theme_colors['title'], font=minutes_font)
    
    current_y = minutes_y + 100
    
    if service_time:
        time_text = f"Service starts at {service_time}"
        time_bbox = draw.textbbox((0, 0), time_text, font=info_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (width - time_width) // 2
        
        outline_width = 2
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((time_x + offset_x, current_y + offset_y), time_text, fill=(0, 0, 0, 200), font=info_font)
        
        draw.text((time_x, current_y), time_text, fill=theme_colors['text'], font=info_font)
        current_y += 60
    
    if welcome_message:
        welcome_bbox = draw.textbbox((0, 0), welcome_message, font=welcome_font)
        welcome_width = welcome_bbox[2] - welcome_bbox[0]
        welcome_x = (width - welcome_width) // 2
        welcome_y = height - 120
        
        outline_width = 2
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text((welcome_x + offset_x, welcome_y + offset_y), welcome_message, fill=(0, 0, 0, 200), font=welcome_font)
        
        draw.text((welcome_x, welcome_y), welcome_message, fill=theme_colors['text'], font=welcome_font)
    
    logo_path = branding.get('logo_path') if branding else None
    img = overlay_logo(img, logo_path, position='top-right', max_width=220)
    
    return img

def generate_obs_scene_collection(readings: dict, service_details: dict, date_str: str, obs_settings: dict | None = None) -> dict:
    """
    Generate an OBS scene collection JSON structure
    that references the exported Worship folder assets with absolute paths
    """
    sources = []
    scenes = []
    source_counter = 1
    
    # Get path settings with defaults
    if obs_settings is None:
        obs_settings = {
            'operatingSystem': 'windows',
            'basePath': 'C:\\Users\\YourName\\Documents\\'
        }
    
    os_type = obs_settings.get('operatingSystem', 'windows')
    base_path = obs_settings.get('basePath', '')
    
    # Determine path separator based on OS
    if os_type == 'windows':
        separator = '\\'
    else:
        separator = '/'
    
    # Helper function to construct absolute path
    def make_absolute_path(relative_path: str) -> str:
        # Replace forward slashes with OS-appropriate separator
        path = relative_path.replace('/', separator)
        # Combine base path with relative path
        if base_path:
            # Ensure base_path ends with separator
            base = base_path if base_path.endswith(separator) else base_path + separator
            return base + path
        return path
    
    # Helper function to create a text source definition
    def create_text_source_def(name: str, file_path: str):
        source_uuid = str(uuid.uuid4())
        source = {
            "versioned_id": "text_gdiplus_v2",
            "name": name,
            "uuid": source_uuid,
            "id": "text_gdiplus_v2",
            "settings": {
                "file": file_path,
                "read_from_file": True,
                "font": {
                    "face": "Arial",
                    "size": 48,
                    "style": "Bold"
                },
                "color": 4294967295,
                "outline": True,
                "outline_size": 2,
                "outline_color": 4278190080,
                "valign": "top",
                "align": "left"
            },
            "mixers": 0,
            "sync": 0,
            "flags": 0,
            "volume": 1.0,
            "balance": 0.5,
            "filters": [],
            "private_settings": {}
        }
        return source, source_uuid
    
    # Helper function to create an image source definition
    def create_image_source_def(name: str, file_path: str):
        source_uuid = str(uuid.uuid4())
        source = {
            "versioned_id": "image_source",
            "name": name,
            "uuid": source_uuid,
            "id": "image_source",
            "settings": {
                "file": file_path,
                "unload": False
            },
            "mixers": 0,
            "sync": 0,
            "flags": 0,
            "volume": 1.0,
            "balance": 0.5,
            "filters": [],
            "private_settings": {}
        }
        return source, source_uuid
    
    # Helper function to create a scene item
    def create_scene_item(source_uuid: str, name: str, x: int, y: int, item_id: int):
        return {
            "id": item_id,
            "name": name,
            "source_uuid": source_uuid,
            "pos": {"x": x, "y": y},
            "scale": {"x": 1.0, "y": 1.0},
            "rot": 0,
            "bounds": {"x": 0, "y": 0},
            "bounds_type": 0,
            "crop_left": 0,
            "crop_top": 0,
            "crop_right": 0,
            "crop_bottom": 0,
            "visible": True,
            "locked": False
        }
    
    # Create title card scene (full-screen)
    title_card_source, title_card_uuid = create_image_source_def(
        "Title Card",
        make_absolute_path("Worship/Title_Card.png")
    )
    sources.append(title_card_source)
    
    title_card_scene = {
        "name": "Title Card",
        "id": 1,
        "sources": [
            create_scene_item(title_card_uuid, "Title Card", 0, 0, source_counter)
        ]
    }
    source_counter += 1
    scenes.append(title_card_scene)
    
    # Create sources and scenes for each scripture reading
    for reading_type, reading_data in readings.items():
        base_name = reading_type.replace('_', ' ').title()
        
        # Lower third image source and scene
        img_source, img_uuid = create_image_source_def(
            f"{base_name} Graphic",
            make_absolute_path(f"Worship/lower_thirds/{base_name}.png")
        )
        sources.append(img_source)
        
        scene = {
            "name": f"{base_name} - Lower Third",
            "id": len(scenes) + 1,
            "sources": [
                create_scene_item(img_uuid, f"{base_name} Graphic", 0, 0, source_counter)
            ]
        }
        source_counter += 1
        scenes.append(scene)
        
        # Text sources and scene
        ref_source, ref_uuid = create_text_source_def(
            f"{base_name} Reference",
            make_absolute_path(f"Worship/readings/{base_name} Reference.txt")
        )
        sources.append(ref_source)
        
        text_source, text_uuid = create_text_source_def(
            f"{base_name} Text",
            make_absolute_path(f"Worship/readings/{base_name}.txt")
        )
        sources.append(text_source)
        
        text_scene = {
            "name": f"{base_name} - Full Text",
            "id": len(scenes) + 1,
            "sources": [
                create_scene_item(ref_uuid, f"{base_name} Reference", 100, 100, source_counter),
                create_scene_item(text_uuid, f"{base_name} Text", 100, 200, source_counter + 1)
            ]
        }
        source_counter += 2
        scenes.append(text_scene)
    
    # Create sources and scenes for hymns
    hymn_fields = {
        'openingHymn': 'Opening Hymn',
        'sequenceHymn': 'Sequence Hymn',
        'communionMotet': 'Communion Motet',
        'closingHymn': 'Closing Hymn'
    }
    
    for field_key, field_label in hymn_fields.items():
        if service_details.get(field_key):
            # Lower third for hymn
            hymn_img_source, hymn_img_uuid = create_image_source_def(
                f"{field_label} Graphic",
                make_absolute_path(f"Worship/lower_thirds/{field_label}.png")
            )
            sources.append(hymn_img_source)
            
            hymn_scene = {
                "name": f"{field_label} - Lower Third",
                "id": len(scenes) + 1,
                "sources": [
                    create_scene_item(hymn_img_uuid, f"{field_label} Graphic", 0, 0, source_counter)
                ]
            }
            source_counter += 1
            scenes.append(hymn_scene)
            
            # Text for hymn
            hymn_title_source, hymn_title_uuid = create_text_source_def(
                f"{field_label} Title",
                make_absolute_path(f"Worship/service_details/{field_label}.txt")
            )
            sources.append(hymn_title_source)
            
            hymn_text_source, hymn_text_uuid = create_text_source_def(
                f"{field_label} Full Text",
                make_absolute_path(f"Worship/service_details/{field_label} Text.txt")
            )
            sources.append(hymn_text_source)
            
            hymn_text_scene = {
                "name": f"{field_label} - Text",
                "id": len(scenes) + 1,
                "sources": [
                    create_scene_item(hymn_title_uuid, f"{field_label} Title", 100, 100, source_counter),
                    create_scene_item(hymn_text_uuid, f"{field_label} Full Text", 100, 200, source_counter + 1)
                ]
            }
            source_counter += 2
            scenes.append(hymn_text_scene)
    
    # Create scene order array
    scene_order = [{"name": scene["name"]} for scene in scenes]
    
    # Create the complete scene collection structure (OBS format)
    scene_collection = {
        "current_scene": scenes[0]["name"] if scenes else "",
        "current_program_scene": scenes[0]["name"] if scenes else "",
        "scene_order": scene_order,
        "name": f"Worship Service {date_str}",
        "sources": sources,
        "scenes": scenes,
        "transitions": [
            {"name": "Fade", "id": "fade_transition"},
            {"name": "Cut", "id": "cut_transition"}
        ],
        "current_transition": "Fade",
        "transition_duration": 300,
        "scaling_enabled": False,
        "scaling_level": 0,
        "scaling_off_x": 0.0,
        "scaling_off_y": 0.0
    }
    
    return scene_collection

@app.route('/api/preview_graphics', methods=['POST'])
def preview_graphics():
    """Generate preview images for title card and lower thirds"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        date_str = data.get('date')
        service_details = data.get('serviceDetails', {})
        service_type = data.get('serviceType', 'eucharist')  # Get service type
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'No date provided'
            }), 400
        
        # Get readings for the date with service type
        calendar_instance = WebLiturgicalCalendar()
        readings = calendar_instance.get_readings_for_date(date_str, service_type=service_type)
        liturgical_info = calendar_instance.get_liturgical_info(datetime.fromisoformat(date_str).date())
        
        if not readings:
            return jsonify({
                'success': False,
                'error': 'No readings available for this date'
            }), 400
        
        previews = []
        
        # Generate title card preview with just the liturgical reference and date
        selected_date = datetime.fromisoformat(date_str)
        formatted_date = selected_date.strftime("%B %d, %Y")
        
        # Get the liturgical name - prefer feast day, then proper Sunday name, then API celebration
        if liturgical_info.get('feast_day'):
            liturgical_name = liturgical_info['feast_day']
        elif liturgical_info.get('is_sunday'):
            liturgical_name = calendar_instance.get_sunday_name(selected_date)
        else:
            readings_data = calendar_instance.liturgy_fetcher.fetch_daily_readings(selected_date)
            liturgical_name = readings_data.get('celebration', 'Sunday Service') if readings_data else 'Sunday Service'
        
        # Remove "(Proper X)" pattern from the liturgical name (e.g., "Twentieth Sunday after Pentecost (Proper 25)" -> "Twentieth Sunday after Pentecost")
        import re
        liturgical_name = re.sub(r'\s*\(Proper \d+\)$', '', liturgical_name)
        
        # Just use the liturgical name without "Holy Eucharist for" prefix
        title_reference = f"{liturgical_name}\n{formatted_date}"
        title_card = create_title_card(title_reference, date_str, branding=branding, style=style)
        
        # Convert title card to base64
        title_buffer = io.BytesIO()
        title_card.save(title_buffer, format='PNG')
        title_buffer.seek(0)
        title_b64 = base64.b64encode(title_buffer.read()).decode('utf-8')
        
        previews.append({
            'name': 'Title Card',
            'image': f'data:image/png;base64,{title_b64}'
        })
        
        # Generate lower thirds previews for ALL readings (not limited)
        # Check for user overrides in service details based on service type
        if service_type == 'evensong':
            # For Evensong, use different field names
            reading_ref_overrides = {
                'first_reading': service_details.get('firstLesson', '').strip(),
                'second_reading': service_details.get('secondLesson', '').strip()
            }
        else:
            # For Eucharist, use traditional field names
            reading_ref_overrides = {
                'first_reading': service_details.get('firstReadingRef', '').strip(),
                'psalm': service_details.get('psalmRef', '').strip(),
                'second_reading': service_details.get('secondReadingRef', '').strip(),
                'gospel': service_details.get('gospelRef', '').strip()
            }
        
        for reading_type in readings.keys():
            reading_data = readings[reading_type]
            # Use override if provided, otherwise use lectionary reference
            reference = reading_ref_overrides.get(reading_type, '') or reading_data.get('reference', '')
            formatted_type = reading_type.replace('_', ' ').title()
            
            # Create lower third image
            lower_third = create_lower_third(reading_type, reference, date_str, branding=branding, style=style)
            
            # Convert to base64
            lt_buffer = io.BytesIO()
            lower_third.save(lt_buffer, format='PNG')
            lt_buffer.seek(0)
            lt_b64 = base64.b64encode(lt_buffer.read()).decode('utf-8')
            
            previews.append({
                'name': formatted_type,
                'image': f'data:image/png;base64,{lt_b64}'
            })
        
        # Generate lower thirds for service details (hymns, musicians, clergy)
        # Different fields for Eucharist vs Evensong
        if service_type == 'evensong':
            # Evensong-specific fields
            service_detail_fields = {
                'officeHymn': 'Office Hymn',
                'magnificatSetting': 'Magnificat',
                'nuncDimittisSetting': 'Nunc Dimittis',
                'anthem': 'Anthem',
                'hymn': 'Hymn',
                'postlude': 'Postlude'
            }
        else:
            # Eucharist fields
            service_detail_fields = {
                'openingHymn': 'Opening Hymn',
                'sequenceHymn': 'Sequence Hymn',
                'offertory': 'Offertory',
                'communionMotet': 'Communion Motet',
                'communionHymn': 'Communion Hymn',
                'closingHymn': 'Closing Hymn',
                'preludeName': 'Prelude',
                'postludeName': 'Postlude'
            }
        
        for field_key, field_label in service_detail_fields.items():
            field_value = service_details.get(field_key, '').strip()
            if field_value:  # Only create graphic if field has content
                # Create lower third image
                lower_third = create_lower_third(field_label, field_value, date_str, branding=branding, style=style)
                
                # Convert to base64
                lt_buffer = io.BytesIO()
                lower_third.save(lt_buffer, format='PNG')
                lt_buffer.seek(0)
                lt_b64 = base64.b64encode(lt_buffer.read()).decode('utf-8')
                
                previews.append({
                    'name': field_label,
                    'image': f'data:image/png;base64,{lt_b64}'
                })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/preview_special_service', methods=['POST'])
def preview_special_service():
    """Generate preview images for special service graphics"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        service_title = data.get('title', '')
        service_date = data.get('date', '')
        readings = data.get('readings', {})
        service_details = data.get('service_details', {})
        liturgical_season = data.get('liturgical_season', '')
        is_funeral = data.get('is_funeral', False)
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not service_title or not service_date:
            return jsonify({
                'success': False,
                'error': 'Service title and date are required'
            }), 400
        
        previews = []
        
        # Generate title card preview
        selected_date = datetime.fromisoformat(service_date)
        formatted_date = selected_date.strftime("%B %d, %Y")
        title_reference = f"{service_title}\n{formatted_date}"
        title_card = create_title_card(title_reference, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
        
        # Convert to base64
        title_buffer = io.BytesIO()
        title_card.save(title_buffer, format='PNG')
        title_buffer.seek(0)
        title_b64 = base64.b64encode(title_buffer.read()).decode('utf-8')
        
        previews.append({
            'name': 'Title Card',
            'image': f'data:image/png;base64,{title_b64}'
        })
        
        # Generate reading graphics
        reading_types = {
            'gospel': 'Gospel',
            'old_testament': 'Old Testament',
            'epistle': 'Epistle',
            'psalm': 'Psalm'
        }
        
        for reading_key, reading_label in reading_types.items():
            reading_data = readings.get(reading_key, {})
            reference = reading_data.get('reference', '').strip()
            
            if reference:
                lower_third = create_lower_third(reading_label, reference, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
                
                lt_buffer = io.BytesIO()
                lower_third.save(lt_buffer, format='PNG')
                lt_buffer.seek(0)
                lt_b64 = base64.b64encode(lt_buffer.read()).decode('utf-8')
                
                previews.append({
                    'name': reading_label,
                    'image': f'data:image/png;base64,{lt_b64}'
                })
        
        # Generate hymn/music graphics
        hymn_fields = {
            'openingHymn': 'Opening Hymn',
            'sequenceHymn': 'Sequence Hymn',
            'offertory': 'Offertory',
            'communionMotet': 'Communion Motet',
            'communionHymn': 'Communion Hymn',
            'closingHymn': 'Closing Hymn'
        }
        
        for field_key, field_label in hymn_fields.items():
            hymn_value = service_details.get(field_key, '').strip()
            if hymn_value:
                lower_third = create_lower_third(field_label, hymn_value, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
                
                lt_buffer = io.BytesIO()
                lower_third.save(lt_buffer, format='PNG')
                lt_buffer.seek(0)
                lt_b64 = base64.b64encode(lt_buffer.read()).decode('utf-8')
                
                previews.append({
                    'name': field_label,
                    'image': f'data:image/png;base64,{lt_b64}'
                })
        
        # Generate blank template preview
        blank_template = create_blank_lower_third(service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, style=style)
        blank_buffer = io.BytesIO()
        blank_template.save(blank_buffer, format='PNG')
        blank_buffer.seek(0)
        blank_b64 = base64.b64encode(blank_buffer.read()).decode('utf-8')
        
        previews.append({
            'name': 'Blank Template',
            'image': f'data:image/png;base64,{blank_b64}'
        })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export_all', methods=['POST'])
def export_all():
    """Combined export: readings text files + lower third graphics in one ZIP"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        service_details = data.get('serviceDetails', {})
        service_type = data.get('serviceType', 'eucharist')  # Get service type
        obs_settings = data.get('obsSettings', {})
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'No date provided'
            }), 400
        
        branding = load_branding_config()
        
        # Parse date for folder naming
        selected_date = datetime.fromisoformat(date_str)
        date_folder_name = "Worship"
        
        # Get readings for the date with service type
        calendar_instance = WebLiturgicalCalendar()
        readings = calendar_instance.get_readings_for_date(date_str, service_type=service_type)
        liturgical_info = calendar_instance.get_liturgical_info(selected_date.date())
        
        if not readings:
            return jsonify({
                'success': False,
                'error': f'No readings available for this date ({service_type})'
            }), 400
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # ===== PART 1: Export text files (from export_readings) =====
            # Create individual text files for each reading
            for reading_type, reading_data in readings.items():
                # Clean reading type name for filename
                base_name = reading_type.replace('_', ' ').title()
                
                # Create text file with formatted scripture text (50 char width)
                text_filename = f"{base_name}.txt"
                text_filepath = f"{date_folder_name}/readings/{text_filename}"
                raw_text = reading_data.get('text', '')
                if raw_text:
                    formatted_text = format_text_with_paragraphs(raw_text, width=50)
                else:
                    formatted_text = raw_text
                zip_file.writestr(text_filepath, formatted_text)
                
                # Create reference file with formatted reference
                ref_filename = f"{base_name} Reference.txt"
                ref_filepath = f"{date_folder_name}/readings/{ref_filename}"
                raw_ref = reading_data.get('reference', '')
                if raw_ref:
                    formatted_ref = textwrap.fill(raw_ref, width=50, break_long_words=False, break_on_hyphens=False)
                else:
                    formatted_ref = raw_ref
                zip_file.writestr(ref_filepath, formatted_ref)
            
            # Create individual service detail files if provided
            if service_details:
                # Handle different fields for Eucharist vs Evensong
                if service_type == 'evensong':
                    # Evensong-specific service details
                    evensong_detail_fields = {
                        'responsoryComposer': 'Responsory Composer',
                        'precesResponsesSetting': 'Preces and Responses Setting',
                        'precesResponsesComposer': 'Preces and Responses Composer',
                        'officeHymn': 'Office Hymn',
                        'firstPsalmRef': 'First Psalm Reference',
                        'firstPsalmComposer': 'First Psalm Composer',
                        'secondPsalmRef': 'Second Psalm Reference',
                        'secondPsalmComposer': 'Second Psalm Composer',
                        'magnificatSetting': 'Magnificat Setting',
                        'magnificatComposer': 'Magnificat Composer',
                        'nuncDimittisSetting': 'Nunc Dimittis Setting',
                        'nuncDimittisComposer': 'Nunc Dimittis Composer',
                        'responsesSetting': 'Responses Setting',
                        'responsesComposer': 'Responses Composer',
                        'anthem': 'Anthem',
                        'hymn': 'Hymn',
                        'postlude': 'Postlude'
                    }
                    
                    for field_key, field_label in evensong_detail_fields.items():
                        field_value = service_details.get(field_key, '').strip()
                        if field_value:
                            formatted_value = textwrap.fill(field_value, width=50, break_long_words=False, break_on_hyphens=False)
                            zip_file.writestr(f"{date_folder_name}/service_details/{field_label}.txt", formatted_value)
                    
                    # Fetch hymn text for Office Hymn and Hymn
                    if service_details.get('officeHymn'):
                        hymn_text = fetch_hymn_text_from_hymnary(service_details['officeHymn'])
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        zip_file.writestr(f"{date_folder_name}/service_details/Office Hymn Text.txt", formatted_hymn_text)
                    
                    if service_details.get('hymn'):
                        hymn_text = fetch_hymn_text_from_hymnary(service_details['hymn'])
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        zip_file.writestr(f"{date_folder_name}/service_details/Hymn Text.txt", formatted_hymn_text)
                else:
                    # Eucharist-specific service details
                    # Individual hymn files with text from Hymnary.org
                    if service_details.get('openingHymn'):
                        formatted_hymn = textwrap.fill(service_details['openingHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Opening Hymn.txt", formatted_hymn)
                        
                        hymn_text = fetch_hymn_text_from_hymnary(service_details['openingHymn'])
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        zip_file.writestr(f"{date_folder_name}/service_details/Opening Hymn Text.txt", formatted_hymn_text)
                    
                    if service_details.get('sequenceHymn'):
                        formatted_hymn = textwrap.fill(service_details['sequenceHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Sequence Hymn.txt", formatted_hymn)
                        
                        hymn_text = fetch_hymn_text_from_hymnary(service_details['sequenceHymn'])
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        zip_file.writestr(f"{date_folder_name}/service_details/Sequence Hymn Text.txt", formatted_hymn_text)
                    
                    if service_details.get('communionMotet'):
                        formatted_motet = textwrap.fill(service_details['communionMotet'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Communion Motet.txt", formatted_motet)
                    
                    if service_details.get('closingHymn'):
                        formatted_hymn = textwrap.fill(service_details['closingHymn'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Closing Hymn.txt", formatted_hymn)
                        
                        hymn_text = fetch_hymn_text_from_hymnary(service_details['closingHymn'])
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        zip_file.writestr(f"{date_folder_name}/service_details/Closing Hymn Text.txt", formatted_hymn_text)
                    
                    # Individual musician files
                    if service_details.get('organistName'):
                        formatted_organist = textwrap.fill(service_details['organistName'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Organist.txt", formatted_organist)
                    
                    if service_details.get('preludeName'):
                        formatted_prelude = textwrap.fill(service_details['preludeName'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Prelude.txt", formatted_prelude)
                    
                    if service_details.get('postludeName'):
                        formatted_postlude = textwrap.fill(service_details['postludeName'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Postlude.txt", formatted_postlude)
                    
                    # Individual clergy files
                    if service_details.get('preacherName'):
                        formatted_preacher = textwrap.fill(service_details['preacherName'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Preacher.txt", formatted_preacher)
                    
                    if service_details.get('presiderName'):
                        formatted_presider = textwrap.fill(service_details['presiderName'], width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(f"{date_folder_name}/service_details/Presider.txt", formatted_presider)
            
            # ===== PART 2: Generate lower third graphics =====
            # Check for liturgical season override in service details
            liturgical_season_override = service_details.get('serviceLiturgicalSeason', '').strip() or None
            is_funeral_service = (liturgical_season_override == 'memorial')
            
            # Generate full-screen title card with just the liturgical reference and date
            # Format date nicely (e.g., "October 19, 2025")
            formatted_date = selected_date.strftime("%B %d, %Y")
            
            # Get the liturgical name - prefer feast day, then proper Sunday name, then API celebration
            if liturgical_info.get('feast_day'):
                liturgical_name = liturgical_info['feast_day']
            elif liturgical_info.get('is_sunday'):
                liturgical_name = calendar_instance.get_sunday_name(selected_date)
            else:
                readings_data = calendar_instance.liturgy_fetcher.fetch_daily_readings(selected_date)
                liturgical_name = readings_data.get('celebration', 'Sunday Service') if readings_data else 'Sunday Service'
            
            # Remove "(Proper X)" pattern from the liturgical name (e.g., "Twentieth Sunday after Pentecost (Proper 25)" -> "Twentieth Sunday after Pentecost")
            import re
            liturgical_name = re.sub(r'\s*\(Proper \d+\)$', '', liturgical_name)
            
            # Just use the liturgical name without "Holy Eucharist for" prefix
            title_reference = f"{liturgical_name}\n{formatted_date}"
            
            title_card_img = create_title_card(title_reference, date_str, is_funeral=is_funeral_service, liturgical_season=liturgical_season_override, branding=branding, style=style)
            title_card_buffer = io.BytesIO()
            title_card_img.save(title_card_buffer, format='PNG')
            title_card_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/Title_Card.png", title_card_buffer.read())
            
            # Create lower third graphic for each reading
            # Check for user overrides in service details based on service type
            if service_type == 'evensong':
                reading_ref_overrides = {
                    'first_reading': service_details.get('firstLesson', '').strip(),
                    'second_reading': service_details.get('secondLesson', '').strip()
                }
            else:
                reading_ref_overrides = {
                    'first_reading': service_details.get('firstReadingRef', '').strip(),
                    'psalm': service_details.get('psalmRef', '').strip(),
                    'second_reading': service_details.get('secondReadingRef', '').strip(),
                    'gospel': service_details.get('gospelRef', '').strip()
                }
            
            for reading_type, reading_data in readings.items():
                # Use override if provided, otherwise use lectionary reference
                reference = reading_ref_overrides.get(reading_type, '') or reading_data.get('reference', 'No reference')
                
                # Generate lower third image with liturgical season colors (with optional override)
                img = create_lower_third(reading_type, reference, date_str, is_funeral=is_funeral_service, liturgical_season=liturgical_season_override, branding=branding, style=style)
                
                # Save image to buffer
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Add to ZIP with proper filename
                filename = f"{reading_type.replace('_', ' ').title()}.png"
                filepath = f"{date_folder_name}/lower_thirds/{filename}"
                zip_file.writestr(filepath, img_buffer.read())
            
            # Create lower third graphics for hymns and music
            # Different fields for Eucharist vs Evensong
            if service_type == 'evensong':
                service_detail_graphics = {
                    'officeHymn': 'Office Hymn',
                    'magnificatSetting': 'Magnificat',
                    'nuncDimittisSetting': 'Nunc Dimittis',
                    'anthem': 'Anthem',
                    'hymn': 'Hymn',
                    'postlude': 'Postlude'
                }
            else:
                service_detail_graphics = {
                    'openingHymn': 'Opening Hymn',
                    'sequenceHymn': 'Sequence Hymn',
                    'offertory': 'Offertory',
                    'communionMotet': 'Communion Motet',
                    'communionHymn': 'Communion Hymn',
                    'closingHymn': 'Closing Hymn',
                    'preludeName': 'Prelude',
                    'postludeName': 'Postlude'
                }
            
            for field_key, field_label in service_detail_graphics.items():
                field_value = service_details.get(field_key, '').strip()
                if field_value:  # Only create graphic if field has content
                    # Generate lower third image with liturgical season colors (with optional override)
                    img = create_lower_third(field_label, field_value, date_str, is_funeral=is_funeral_service, liturgical_season=liturgical_season_override, branding=branding, style=style)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP with proper filename
                    filename = f"{field_label}.png"
                    filepath = f"{date_folder_name}/lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
            
            # ===== Generate blank lower third template for manual use =====
            blank_template = create_blank_lower_third(date_str, is_funeral=is_funeral_service, liturgical_season=liturgical_season_override, style=style)
            blank_buffer = io.BytesIO()
            blank_template.save(blank_buffer, format='PNG')
            blank_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/BLANK_TEMPLATE.png", blank_buffer.read())
            
            # ===== PART 3: Generate OBS Scene Collection =====
            obs_collection = generate_obs_scene_collection(readings, service_details, date_str, obs_settings)
            obs_json = json.dumps(obs_collection, indent=2)
            zip_file.writestr(f"{date_folder_name}_OBS_Scenes.json", obs_json)
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name="Worship.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate combined export'
        }), 500

@app.route('/api/generate_lower_thirds', methods=['POST'])
def generate_lower_thirds():
    """Generate lower third graphics for broadcast use"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not date_str:
            return jsonify({
                'success': False,
                'error': 'No date provided'
            }), 400
        
        branding = load_branding_config()
        
        # Parse date for folder naming
        selected_date = datetime.fromisoformat(date_str)
        date_folder_name = selected_date.strftime("%Y-%m-%d")
        
        # Get readings for the date
        calendar_instance = WebLiturgicalCalendar()
        readings = calendar_instance.get_readings_for_date(date_str)
        
        if not readings:
            return jsonify({
                'success': False,
                'error': 'No readings available for this date'
            }), 400
        
        # Get service details for hymns/music
        details_file = 'service_details.json'
        service_details = {}
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r') as f:
                    service_data = json.load(f)
                    service_details = service_data.get(date_str, {})
            except:
                service_details = {}
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create lower third graphic for each reading
            for reading_type, reading_data in readings.items():
                reference = reading_data.get('reference', 'No reference')
                
                # Generate lower third image with liturgical season colors
                img = create_lower_third(reading_type, reference, date_str, branding=branding, style=style)
                
                # Save image to buffer
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Add to ZIP with proper filename
                filename = f"{reading_type.replace('_', ' ').title()}.png"
                filepath = f"{date_folder_name}_lower_thirds/{filename}"
                zip_file.writestr(filepath, img_buffer.read())
            
            # Create lower third graphics for hymns and music
            hymn_fields = {
                'openingHymn': 'Opening Hymn',
                'sequenceHymn': 'Sequence Hymn',
                'offertory': 'Offertory',
                'communionMotet': 'Communion Motet',
                'communionHymn': 'Communion Hymn',
                'closingHymn': 'Closing Hymn',
                'preludeTitle': 'Prelude Title',
                'postludeTitle': 'Postlude Title'
            }
            
            for field_key, field_label in hymn_fields.items():
                hymn_value = service_details.get(field_key, '').strip()
                if hymn_value:  # Only create graphic if field has content
                    # Generate lower third image with liturgical season colors and branding
                    img = create_lower_third(field_label, hymn_value, date_str, branding=branding, style=style)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP with proper filename
                    filename = f"{field_label}.png"
                    filepath = f"{date_folder_name}_lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=f"lower_thirds_{date_folder_name}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate lower thirds'
        }), 500

@app.route('/api/generate_custom_title_card', methods=['POST'])
def generate_custom_title_card():
    """Generate a custom title card with user-specified text"""
    try:
        data = request.get_json()
        custom_text = data.get('customText', '').strip()
        liturgical_season = data.get('liturgicalSeason')  # Optional: liturgical season for colors
        is_funeral = data.get('isFuneral', False)  # Optional: for black/white theme
        style = data.get('style', 'classic')  # Get style for Christmas Trinity, etc.
        
        if not custom_text:
            return jsonify({
                'success': False,
                'error': 'No text provided for title card'
            }), 400
        
        branding = load_branding_config()
        
        # Generate the title card using the existing function
        title_card_img = create_title_card(custom_text, liturgical_season=liturgical_season, is_funeral=is_funeral, branding=branding, style=style)
        
        # Convert to PNG and send as file download
        img_buffer = io.BytesIO()
        title_card_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Create a filename from the custom text (sanitized)
        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in custom_text)
        safe_filename = safe_filename[:50]  # Limit length
        safe_filename = safe_filename.strip() or 'Custom_Title_Card'
        
        return send_file(
            io.BytesIO(img_buffer.read()),
            as_attachment=True,
            download_name=f"{safe_filename}.png",
            mimetype='image/png'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate custom title card'
        }), 500

@app.route('/api/generate_custom_lower_third', methods=['POST'])
def generate_custom_lower_third():
    """Generate a custom lower third with user-provided text and liturgical season"""
    try:
        data = request.get_json()
        label_text = data.get('labelText', '').strip()
        content_text = data.get('contentText', '').strip()
        liturgical_season_raw = data.get('liturgicalSeason')
        liturgical_season = liturgical_season_raw.strip() if liturgical_season_raw else ''
        is_memorial = data.get('isMemorial', False)
        style = data.get('style', 'classic')
        
        # Validate that at least one field has content
        if not label_text and not content_text:
            return jsonify({
                'success': False,
                'error': 'At least one field (Label or Content) must be provided'
            }), 400
        
        branding = load_branding_config()
        
        # Generate the lower third using the existing function
        # The create_lower_third function takes reading_type and reference as parameters
        lower_third_img = create_lower_third(
            reading_type=label_text or '',
            reference=content_text or '',
            liturgical_season=liturgical_season if liturgical_season else None,
            is_funeral=is_memorial,
            branding=branding,
            style=style
        )
        
        # Convert to PNG and send as file download
        img_buffer = io.BytesIO()
        lower_third_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Create a filename from the label or content text (sanitized)
        filename_base = label_text or content_text
        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in filename_base)
        safe_filename = safe_filename[:50]  # Limit length
        safe_filename = safe_filename.strip() or 'Custom_Lower_Third'
        
        return send_file(
            io.BytesIO(img_buffer.read()),
            as_attachment=True,
            download_name=f"{safe_filename}_Lower_Third.png",
            mimetype='image/png'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate custom lower third'
        }), 500

@app.route('/api/preview_custom_lower_third', methods=['POST'])
def preview_custom_lower_third():
    """Generate preview for custom lower third"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        label_text = data.get('labelText', '').strip()
        content_text = data.get('contentText', '').strip()
        liturgical_season_raw = data.get('liturgicalSeason')
        liturgical_season = liturgical_season_raw.strip() if liturgical_season_raw else ''
        is_memorial = data.get('isMemorial', False)
        style = data.get('style', 'classic')
        
        # Validate that at least one field is provided
        if not label_text and not content_text:
            return jsonify({
                'success': False,
                'error': 'At least one field (Label or Content) must be provided'
            }), 400
        
        # Generate the lower third using the existing function
        lower_third_img = create_lower_third(
            reading_type=label_text or '',
            reference=content_text or '',
            liturgical_season=liturgical_season if liturgical_season else None,
            is_funeral=is_memorial,
            branding=branding,
            style=style
        )
        
        # Convert to base64
        img_buffer = io.BytesIO()
        lower_third_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        previews = [{
            'name': 'Custom Lower Third',
            'image': f'data:image/png;base64,{img_b64}'
        }]
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate preview'
        }), 500

@app.route('/api/preview_announcements', methods=['POST'])
def preview_announcements():
    """Generate preview images for all announcements in the batch"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        announcements = data.get('announcements', [])
        style = data.get('style', 'classic')
        
        if not announcements:
            return jsonify({
                'success': False,
                'error': 'No announcements provided'
            }), 400
        
        previews = []
        
        for idx, announcement in enumerate(announcements, 1):
            ann_type = announcement.get('type', 'general')
            title = announcement.get('title', '')
            
            ann_img = create_announcement_slide(announcement, branding=branding, style=style)
            
            img_buffer = io.BytesIO()
            ann_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            type_labels = {
                'event': 'Event',
                'prayer': 'Prayer',
                'giving': 'Giving',
                'general': 'General'
            }
            type_label = type_labels.get(ann_type, 'Announcement')
            
            previews.append({
                'name': f'Announcement {idx}: {type_label} - {title[:30]}{"..." if len(title) > 30 else ""}',
                'image': f'data:image/png;base64,{img_b64}'
            })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate announcement previews'
        }), 500

@app.route('/api/generate_announcements', methods=['POST'])
def generate_announcements():
    """Generate and download ZIP file containing all announcement slides"""
    try:
        data = request.get_json()
        announcements = data.get('announcements', [])
        style = data.get('style', 'classic')
        
        if not announcements:
            return jsonify({
                'success': False,
                'error': 'No announcements provided'
            }), 400
        
        branding = load_branding_config()
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, announcement in enumerate(announcements, 1):
                ann_type = announcement.get('type', 'general')
                title = announcement.get('title', '')
                
                ann_img = create_announcement_slide(announcement, branding=branding, style=style)
                
                img_buffer = io.BytesIO()
                ann_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                type_labels = {
                    'event': 'Event',
                    'prayer': 'Prayer',
                    'giving': 'Giving',
                    'general': 'General'
                }
                type_label = type_labels.get(ann_type, 'Announcement')
                
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
                safe_title = safe_title[:30].strip() or type_label
                
                filename = f"Announcement_{idx}_{type_label}_{safe_title}.png"
                zip_file.writestr(filename, img_buffer.read())
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'Announcements_{timestamp}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate announcements'
        }), 500

@app.route('/api/preview_service_order', methods=['POST'])
def preview_service_order():
    """Generate preview images for all service order items"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        order_items = data.get('orderItems', [])
        liturgical_season = data.get('liturgicalSeason')
        is_memorial = data.get('isMemorial', False)
        show_numbering = data.get('showNumbering', False)
        
        if not order_items:
            return jsonify({
                'success': False,
                'error': 'No service order items provided'
            }), 400
        
        previews = []
        
        for idx, item_text in enumerate(order_items, 1):
            if not item_text.strip():
                continue
            
            order_img = create_service_order_slide(
                order_item=item_text,
                liturgical_season=liturgical_season if liturgical_season else None,
                is_memorial=is_memorial,
                show_number=show_numbering,
                item_number=idx,
                branding=branding
            )
            
            img_buffer = io.BytesIO()
            order_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            previews.append({
                'name': f'Order {idx}: {item_text[:40]}{"..." if len(item_text) > 40 else ""}',
                'image': f'data:image/png;base64,{img_b64}'
            })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate service order previews'
        }), 500

@app.route('/api/generate_service_order', methods=['POST'])
def generate_service_order():
    """Generate and download ZIP file containing all service order slides"""
    try:
        data = request.get_json()
        order_items = data.get('orderItems', [])
        liturgical_season = data.get('liturgicalSeason')
        is_memorial = data.get('isMemorial', False)
        show_numbering = data.get('showNumbering', False)
        
        if not order_items:
            return jsonify({
                'success': False,
                'error': 'No service order items provided'
            }), 400
        
        branding = load_branding_config()
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, item_text in enumerate(order_items, 1):
                if not item_text.strip():
                    continue
                
                order_img = create_service_order_slide(
                    order_item=item_text,
                    liturgical_season=liturgical_season if liturgical_season else None,
                    is_memorial=is_memorial,
                    show_number=show_numbering,
                    item_number=idx,
                    branding=branding
                )
                
                img_buffer = io.BytesIO()
                order_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                safe_item = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item_text)
                safe_item = safe_item[:40].strip() or f'Item_{idx}'
                
                filename = f"Order_{idx:02d}_{safe_item}.png"
                zip_file.writestr(filename, img_buffer.read())
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'Service_Order_{timestamp}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate service order slides'
        }), 500

@app.route('/api/preview_countdown', methods=['POST'])
def preview_countdown():
    """Generate preview images for all countdown timer slides"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        times = data.get('times', [])
        custom_time = data.get('customTime')
        liturgical_season = data.get('liturgicalSeason')
        is_memorial = data.get('isMemorial', False)
        welcome_message = data.get('welcomeMessage', '').strip()
        service_time = data.get('serviceTime', '').strip()
        style = data.get('style', 'classic')
        
        all_times = list(times)
        if custom_time and custom_time > 0:
            all_times.append(custom_time)
        
        if not all_times:
            return jsonify({
                'success': False,
                'error': 'No countdown times selected'
            }), 400
        
        previews = []
        
        for minutes in sorted(all_times, reverse=True):
            countdown_img = create_countdown_slide(
                minutes=minutes,
                liturgical_season=liturgical_season if liturgical_season else None,
                is_memorial=is_memorial,
                welcome_message=welcome_message if welcome_message else None,
                service_time=service_time if service_time else None,
                branding=branding,
                style=style
            )
            
            img_buffer = io.BytesIO()
            countdown_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            previews.append({
                'name': f'Countdown: {minutes} minute{"s" if minutes != 1 else ""}',
                'image': f'data:image/png;base64,{img_b64}'
            })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate countdown previews'
        }), 500

@app.route('/api/generate_countdown', methods=['POST'])
def generate_countdown():
    """Generate and download ZIP file containing all countdown timer slides"""
    try:
        data = request.get_json()
        times = data.get('times', [])
        custom_time = data.get('customTime')
        liturgical_season = data.get('liturgicalSeason')
        is_memorial = data.get('isMemorial', False)
        welcome_message = data.get('welcomeMessage', '').strip()
        service_time = data.get('serviceTime', '').strip()
        style = data.get('style', 'classic')
        
        all_times = list(times)
        if custom_time and custom_time > 0:
            all_times.append(custom_time)
        
        if not all_times:
            return jsonify({
                'success': False,
                'error': 'No countdown times selected'
            }), 400
        
        branding = load_branding_config()
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for minutes in sorted(all_times, reverse=True):
                countdown_img = create_countdown_slide(
                    minutes=minutes,
                    liturgical_season=liturgical_season if liturgical_season else None,
                    is_memorial=is_memorial,
                    welcome_message=welcome_message if welcome_message else None,
                    service_time=service_time if service_time else None,
                    branding=branding,
                    style=style
                )
                
                img_buffer = io.BytesIO()
                countdown_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                filename = f"Countdown_{minutes:02d}min.png"
                zip_file.writestr(filename, img_buffer.read())
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'Countdown_Timer_{timestamp}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate countdown timer slides'
        }), 500

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload and text extraction"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Only PDF files are allowed'
            }), 400
        
        # Save uploaded file
        original_filename = file.filename or 'unknown.pdf'
        filename = secure_filename(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        extraction_result = extract_text_from_pdf(filepath)
        
        if not extraction_result['success']:
            # Clean up file on error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': False,
                'error': f"Failed to extract text: {extraction_result['error']}"
            }), 500
        
        # Process liturgical content
        liturgical_result = process_liturgical_pdf(extraction_result['text'])
        
        # Clean up uploaded file after processing
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'page_count': extraction_result['page_count'],
            'extraction_method': extraction_result['method'],
            'text_length': len(extraction_result['text']),
            'sections': liturgical_result['sections'] if liturgical_result['success'] else {},
            'full_text': extraction_result['text'][:1000] + ('...' if len(extraction_result['text']) > 1000 else ''),  # Truncate for response
            'processing_success': liturgical_result['success']
        })
        
    except Exception as e:
        # Clean up file on error
        try:
            if 'filepath' in locals():
                filepath_var = locals().get('filepath')
                if filepath_var and os.path.exists(filepath_var):
                    os.remove(filepath_var)
        except:
            pass
            
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to process PDF file'
        }), 500

@app.route('/api/pdf_uploads', methods=['GET'])
def list_pdf_uploads():
    """List recent PDF upload processing results"""
    try:
        # This could be expanded to show upload history from a database
        # For now, just return basic info about the upload capability
        return jsonify({
            'success': True,
            'upload_enabled': True,
            'max_file_size_mb': MAX_CONTENT_LENGTH // (1024 * 1024),
            'allowed_extensions': list(ALLOWED_EXTENSIONS),
            'message': 'PDF upload functionality is ready'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/special_service', methods=['POST'])
def special_service():
    """Generate graphics and text files for special (non-lectionary) services"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        service_title = data.get('title', '')
        service_date = data.get('date', '')
        readings = data.get('readings', {})
        service_details = data.get('service_details', {})
        liturgical_season = data.get('liturgical_season', '')
        is_funeral = data.get('is_funeral', False)
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not service_title:
            return jsonify({
                'success': False,
                'error': 'Service title is required'
            }), 400
        
        if not service_date:
            return jsonify({
                'success': False,
                'error': 'Service date is required'
            }), 400
        
        # Parse date
        selected_date = datetime.fromisoformat(service_date)
        date_folder_name = "Worship"
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # ===== PART 1: Export text files for readings =====
            reading_types = {
                'gospel': 'Gospel',
                'old_testament': 'Old Testament',
                'epistle': 'Epistle',
                'psalm': 'Psalm'
            }
            
            for reading_key, reading_label in reading_types.items():
                reading_data = readings.get(reading_key, {})
                reference = reading_data.get('reference', '').strip()
                text = reading_data.get('text', '').strip()
                
                if reference or text:
                    # Create text file with scripture text
                    if text:
                        text_filename = f"{reading_label}.txt"
                        text_filepath = f"{date_folder_name}/readings/{text_filename}"
                        formatted_text = format_text_with_paragraphs(text, width=50)
                        zip_file.writestr(text_filepath, formatted_text)
                    
                    # Create reference file
                    if reference:
                        ref_filename = f"{reading_label} Reference.txt"
                        ref_filepath = f"{date_folder_name}/readings/{ref_filename}"
                        formatted_ref = textwrap.fill(reference, width=50, break_long_words=False, break_on_hyphens=False)
                        zip_file.writestr(ref_filepath, formatted_ref)
            
            # ===== PART 2: Export service details files =====
            service_detail_fields = {
                'openingHymn': 'Opening Hymn',
                'sequenceHymn': 'Sequence Hymn',
                'communionMotet': 'Communion Motet',
                'closingHymn': 'Closing Hymn',
                'organistName': 'Organist',
                'preludeName': 'Prelude Title',
                'postludeName': 'Postlude Title',
                'preacherName': 'Preacher',
                'offertory': 'Offertory'
            }
            
            for field_key, field_label in service_detail_fields.items():
                field_value = service_details.get(field_key, '').strip()
                if field_value:
                    formatted_value = textwrap.fill(field_value, width=50, break_long_words=False, break_on_hyphens=False)
                    filename = f"{field_label}.txt"
                    filepath = f"{date_folder_name}/service_details/{filename}"
                    zip_file.writestr(filepath, formatted_value)
            
            # Fetch hymn texts from Hymnary.org
            for hymn_key in ['openingHymn', 'sequenceHymn', 'closingHymn']:
                hymn_value = service_details.get(hymn_key, '').strip()
                if hymn_value:
                    hymn_text = fetch_hymn_text_from_hymnary(hymn_value)
                    if hymn_text:
                        formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                        label = hymn_key.replace('Hymn', ' Hymn').replace('opening', 'Opening').replace('sequence', 'Sequence').replace('closing', 'Closing')
                        filename = f"{label.strip()} Text.txt"
                        filepath = f"{date_folder_name}/service_details/{filename}"
                        zip_file.writestr(filepath, formatted_hymn_text)
            
            # ===== PART 3: Generate title card with service title and date =====
            formatted_date = selected_date.strftime("%B %d, %Y")
            title_reference = f"{service_title}\n{formatted_date}"
            title_card = create_title_card(title_reference, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
            title_card_buffer = io.BytesIO()
            title_card.save(title_card_buffer, format='PNG')
            title_card_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/Title Card.png", title_card_buffer.read())
            
            # ===== PART 4: Generate lower third graphics for readings =====
            for reading_key, reading_label in reading_types.items():
                reading_data = readings.get(reading_key, {})
                reference = reading_data.get('reference', '').strip()
                
                if reference:
                    # Generate lower third image (use funeral colors if flagged, otherwise liturgical colors)
                    img = create_lower_third(reading_label, reference, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP
                    filename = f"{reading_label}.png"
                    filepath = f"{date_folder_name}/lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
            
            # ===== PART 5: Generate lower third graphics for hymns/music =====
            hymn_fields = {
                'openingHymn': 'Opening Hymn',
                'sequenceHymn': 'Sequence Hymn',
                'offertory': 'Offertory',
                'communionMotet': 'Communion Motet',
                'communionHymn': 'Communion Hymn',
                'closingHymn': 'Closing Hymn'
            }
            
            for field_key, field_label in hymn_fields.items():
                hymn_value = service_details.get(field_key, '').strip()
                if hymn_value:
                    # Generate lower third image (use funeral colors if flagged, otherwise liturgical colors)
                    img = create_lower_third(field_label, hymn_value, service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, branding=branding, style=style)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP
                    filename = f"{field_label}.png"
                    filepath = f"{date_folder_name}/lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
            
            # ===== PART 6: Generate blank lower third template for manual use =====
            blank_template = create_blank_lower_third(service_date, is_funeral=is_funeral, liturgical_season=liturgical_season if liturgical_season else None, style=style)
            blank_buffer = io.BytesIO()
            blank_template.save(blank_buffer, format='PNG')
            blank_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/BLANK_TEMPLATE.png", blank_buffer.read())
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        
        # Use consistent "Worship.zip" filename for all service exports
        download_name = "Worship.zip"
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate special service materials'
        }), 500

@app.route('/api/evensong_service', methods=['POST'])
def evensong_service():
    """Generate service details export for Evensong services"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        service_date = data.get('date', '')
        evensong_details = data.get('evensong_details', {})
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not service_date:
            return jsonify({
                'success': False,
                'error': 'Service date is required'
            }), 400
        
        # Parse date
        selected_date = datetime.fromisoformat(service_date)
        date_folder_name = f"Evensong_{service_date.replace('-', '')}"
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # ===== Export Evensong service details as text files =====
            evensong_fields = {
                'responsoryComposer': 'Responsory Composer',
                'precesResponsesSetting': 'Preces and Responses Setting',
                'precesResponsesComposer': 'Preces and Responses Composer',
                'officeHymn': 'Office Hymn',
                'firstPsalmRef': 'First Psalm Reference',
                'firstPsalmComposer': 'First Psalm Composer',
                'secondPsalmRef': 'Second Psalm Reference',
                'secondPsalmComposer': 'Second Psalm Composer',
                'firstLesson': 'The First Lesson',
                'magnificatSetting': 'Magnificat Setting',
                'magnificatComposer': 'Magnificat Composer',
                'secondLesson': 'The Second Lesson',
                'nuncDimittisSetting': 'Nunc Dimittis Setting',
                'nuncDimittisComposer': 'Nunc Dimittis Composer',
                'responsesSetting': 'Responses Setting',
                'responsesComposer': 'Responses Composer',
                'anthem': 'Anthem',
                'hymn': 'Hymn',
                'postlude': 'Postlude'
            }
            
            for field_key, field_label in evensong_fields.items():
                field_value = evensong_details.get(field_key, '').strip()
                if field_value:
                    formatted_value = textwrap.fill(field_value, width=50, break_long_words=False, break_on_hyphens=False)
                    filename = f"{field_label}.txt"
                    filepath = f"{date_folder_name}/service_details/{filename}"
                    zip_file.writestr(filepath, formatted_value)
            
            # Fetch hymn text from Hymnary.org for Office Hymn and Hymn
            office_hymn = evensong_details.get('officeHymn', '').strip()
            if office_hymn:
                hymn_text = fetch_hymn_text_from_hymnary(office_hymn)
                if hymn_text:
                    formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                    filename = "Office Hymn Text.txt"
                    filepath = f"{date_folder_name}/service_details/{filename}"
                    zip_file.writestr(filepath, formatted_hymn_text)
            
            hymn = evensong_details.get('hymn', '').strip()
            if hymn:
                hymn_text = fetch_hymn_text_from_hymnary(hymn)
                if hymn_text:
                    formatted_hymn_text = format_text_with_paragraphs(hymn_text, width=50)
                    filename = "Hymn Text.txt"
                    filepath = f"{date_folder_name}/service_details/{filename}"
                    zip_file.writestr(filepath, formatted_hymn_text)
            
            # ===== Generate title card for Evensong service =====
            formatted_date = selected_date.strftime("%B %d, %Y")
            title_reference = f"Evensong\n{formatted_date}"
            title_card = create_title_card(title_reference, service_date, branding=branding, style=style)
            title_card_buffer = io.BytesIO()
            title_card.save(title_card_buffer, format='PNG')
            title_card_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/Title Card.png", title_card_buffer.read())
            
            # ===== Generate lower third graphics for Evensong elements =====
            lower_third_fields = {
                'officeHymn': 'Office Hymn',
                'firstLesson': 'First Lesson',
                'magnificatSetting': 'Magnificat',
                'secondLesson': 'Second Lesson',
                'nuncDimittisSetting': 'Nunc Dimittis',
                'anthem': 'Anthem',
                'hymn': 'Hymn'
            }
            
            for field_key, field_label in lower_third_fields.items():
                field_value = evensong_details.get(field_key, '').strip()
                if field_value:
                    # Generate lower third image
                    img = create_lower_third(field_label, field_value, service_date, branding=branding, style=style)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP
                    filename = f"{field_label}.png"
                    filepath = f"{date_folder_name}/lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
            
            # ===== Generate blank lower third template for manual use =====
            blank_template = create_blank_lower_third(service_date, style=style)
            blank_buffer = io.BytesIO()
            blank_template.save(blank_buffer, format='PNG')
            blank_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/BLANK_TEMPLATE.png", blank_buffer.read())
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        download_name = f"evensong_service_{service_date.replace('-', '')}.zip"
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate Evensong service materials'
        }), 500

@app.route('/api/concert_program', methods=['POST'])
def concert_program():
    """Generate concert program with title card and lower thirds for each piece"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        performer = data.get('performer', '').strip()
        concert_date = data.get('date', '').strip()
        concert_time = data.get('time', '').strip()
        pieces = data.get('pieces', [])
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not performer:
            return jsonify({
                'success': False,
                'error': 'Performer name is required'
            }), 400
        
        if not concert_date:
            return jsonify({
                'success': False,
                'error': 'Concert date is required'
            }), 400
        
        if not concert_time:
            return jsonify({
                'success': False,
                'error': 'Concert time is required'
            }), 400
        
        # Filter pieces: accept if either title or composer is provided
        filtered_pieces = []
        for piece in pieces:
            title = piece.get('title', '').strip()
            composer = piece.get('composer', '').strip()
            if title or composer:  # Accept if either field has data
                filtered_pieces.append({
                    'title': title,
                    'composer': composer
                })
        
        date_folder_name = f"concert_{concert_date.replace('-', '')}"
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            title_text = f"{performer}\n{concert_date} at {concert_time}"
            # Use Christmas Trinity style for title card if selected, otherwise concert theme
            if style == 'christmas_trinity':
                title_card = create_title_card(title_text, branding=branding, style=style)
            else:
                title_card = create_title_card(title_text, theme='concert', branding=branding)
            title_card_buffer = io.BytesIO()
            title_card.save(title_card_buffer, format='PNG')
            title_card_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/Title_Card.png", title_card_buffer.read())
            
            for idx, piece in enumerate(filtered_pieces, 1):
                # Format text based on available fields
                if piece['title'] and piece['composer']:
                    piece_text = f"{piece['title']} - {piece['composer']}"
                elif piece['title']:
                    piece_text = piece['title']
                else:
                    piece_text = piece['composer']
                
                lower_third = create_lower_third(piece['title'] if piece['title'] else 'Piece', 
                                                piece['composer'] if piece['composer'] else '', 
                                                theme='concert', branding=branding, style=style)
                
                img_buffer = io.BytesIO()
                lower_third.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                filename = f"Piece_{idx}.png"
                filepath = f"{date_folder_name}/lower_thirds/{filename}"
                zip_file.writestr(filepath, img_buffer.read())
        
        zip_buffer.seek(0)
        download_name = f"concert_program_{concert_date.replace('-', '')}.zip"
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate concert program'
        }), 500

@app.route('/api/preview_concert_program', methods=['POST'])
def preview_concert_program():
    """Generate preview images for concert program title card and lower thirds"""
    try:
        branding = load_branding_config()
        
        data = request.get_json()
        performer = data.get('performer', '').strip()
        concert_date = data.get('date', '').strip()
        concert_time = data.get('time', '').strip()
        pieces = data.get('pieces', [])
        style = data.get('style', 'classic')  # Get style for lower thirds
        
        if not performer:
            return jsonify({
                'success': False,
                'error': 'Performer name is required'
            }), 400
        
        if not concert_date:
            return jsonify({
                'success': False,
                'error': 'Concert date is required'
            }), 400
        
        if not concert_time:
            return jsonify({
                'success': False,
                'error': 'Concert time is required'
            }), 400
        
        # Filter pieces: accept if either title or composer is provided
        filtered_pieces = []
        for piece in pieces:
            title = piece.get('title', '').strip()
            composer = piece.get('composer', '').strip()
            if title or composer:  # Accept if either field has data
                filtered_pieces.append({
                    'title': title,
                    'composer': composer
                })
        
        previews = []
        
        # Generate title card preview
        title_text = f"{performer}\n{concert_date} at {concert_time}"
        # Use Christmas Trinity style for title card if selected, otherwise concert theme
        if style == 'christmas_trinity':
            title_card = create_title_card(title_text, branding=branding, style=style)
        else:
            title_card = create_title_card(title_text, theme='concert', branding=branding)
        
        # Convert title card to base64
        title_buffer = io.BytesIO()
        title_card.save(title_buffer, format='PNG')
        title_buffer.seek(0)
        title_b64 = base64.b64encode(title_buffer.read()).decode('utf-8')
        
        previews.append({
            'name': 'Title Card',
            'image': f'data:image/png;base64,{title_b64}'
        })
        
        # Generate lower thirds previews for each piece
        for idx, piece in enumerate(filtered_pieces, 1):
            # Format display name based on available fields
            if piece['title'] and piece['composer']:
                display_name = f'Piece {idx}: {piece["title"]} - {piece["composer"]}'
            elif piece['title']:
                display_name = f'Piece {idx}: {piece["title"]}'
            else:
                display_name = f'Piece {idx}: {piece["composer"]}'
            
            lower_third = create_lower_third(piece['title'] if piece['title'] else 'Piece', 
                                            piece['composer'] if piece['composer'] else '', 
                                            theme='concert', branding=branding, style=style)
            
            # Convert lower third to base64
            img_buffer = io.BytesIO()
            lower_third.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            previews.append({
                'name': f'Piece {idx}: {piece["title"]}',
                'image': f'data:image/png;base64,{img_b64}'
            })
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate concert preview'
        }), 500

@app.route('/wizard')
def wizard():
    """Service Preparation Wizard - step-by-step graphics generation"""
    return render_template('wizard.html')

@app.route('/api/wizard_export', methods=['POST'])
def wizard_export():
    """Generate complete graphics package from wizard data"""
    try:
        data = request.get_json()
        
        date_str = data.get('date')
        service_type = data.get('serviceType', 'eucharist')
        service_details = data.get('serviceDetails', {})
        readings = data.get('readings', {})
        style = data.get('style', 'classic')
        liturgical_override = data.get('liturgicalOverride', '')
        extras = data.get('extras', {})
        
        if not date_str:
            return jsonify({'success': False, 'error': 'No date provided'}), 400
        
        branding = load_branding_config()
        calendar_instance = WebLiturgicalCalendar()
        
        selected_date = datetime.fromisoformat(date_str)
        date_folder_name = selected_date.strftime("%Y-%m-%d")
        
        is_funeral = service_type == 'funeral'
        liturgical_season = liturgical_override if liturgical_override else None
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            liturgical_info = calendar_instance.get_liturgical_info(selected_date.date())
            
            # Get liturgical name - prefer feast day, then proper Sunday name, then API
            if liturgical_info.get('feast_day'):
                liturgical_name = liturgical_info['feast_day']
            elif liturgical_info.get('is_sunday'):
                liturgical_name = calendar_instance.get_sunday_name(selected_date)
            else:
                readings_data = calendar_instance.liturgy_fetcher.fetch_daily_readings(selected_date)
                liturgical_name = readings_data.get('celebration', 'Sunday Service') if readings_data else 'Sunday Service'
            
            formatted_date = selected_date.strftime("%B %d, %Y")
            
            # Format title based on service type
            if service_type == 'eucharist':
                title_text = f"Holy Eucharist for the\n{liturgical_name}\n{formatted_date}"
            elif service_type == 'evensong':
                title_text = f"Evensong for the\n{liturgical_name}\n{formatted_date}"
            elif service_type == 'funeral':
                title_text = f"Funeral Service\n{formatted_date}"
            elif service_type == 'concert':
                title_text = f"Concert\n{formatted_date}"
            else:
                title_text = f"{liturgical_name}\n{formatted_date}"
            
            title_card = create_title_card(
                title_text,
                liturgical_season=liturgical_season,
                is_funeral=is_funeral,
                branding=branding,
                style=style
            )
            img_buffer = io.BytesIO()
            title_card.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/title_cards/Title_Card.png", img_buffer.read())
            
            if readings:
                reading_order = ['first_reading', 'psalm', 'second_reading', 'gospel']
                for reading_key in reading_order:
                    if reading_key in readings and readings[reading_key]:
                        reading_data = readings[reading_key]
                        reference = reading_data.get('reference', '')
                        text = reading_data.get('text', '')
                        
                        reading_name = reading_key.replace('_', ' ').title()
                        
                        lower_third = create_lower_third(
                            reading_type=reading_name,
                            reference=reference,
                            liturgical_season=liturgical_season,
                            is_funeral=is_funeral,
                            branding=branding,
                            style=style
                        )
                        img_buffer = io.BytesIO()
                        lower_third.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        zip_file.writestr(f"{date_folder_name}/lower_thirds/{reading_name.replace(' ', '_')}.png", img_buffer.read())
                        
                        if text:
                            formatted_text = format_text_with_paragraphs(text, width=50)
                            zip_file.writestr(f"{date_folder_name}/readings/{reading_name.replace(' ', '_')}.txt", formatted_text)
                        if reference:
                            zip_file.writestr(f"{date_folder_name}/readings/{reading_name.replace(' ', '_')}_Reference.txt", reference)
            
            service_lower_thirds = []
            
            if service_details.get('preludeTitle'):
                service_lower_thirds.append(('Prelude', service_details['preludeTitle']))
            if service_details.get('openingHymn'):
                service_lower_thirds.append(('Opening Hymn', service_details['openingHymn']))
            if service_details.get('sequenceHymn'):
                service_lower_thirds.append(('Sequence Hymn', service_details['sequenceHymn']))
            if service_details.get('offertoryHymn'):
                service_lower_thirds.append(('Offertory Hymn', service_details['offertoryHymn']))
            if service_details.get('communionMotet'):
                service_lower_thirds.append(('Communion Motet', service_details['communionMotet']))
            if service_details.get('closingHymn'):
                service_lower_thirds.append(('Closing Hymn', service_details['closingHymn']))
            if service_details.get('postludeTitle'):
                service_lower_thirds.append(('Postlude', service_details['postludeTitle']))
            if service_details.get('organistName'):
                service_lower_thirds.append(('Organist', service_details['organistName']))
            if service_details.get('presiderName'):
                service_lower_thirds.append(('Presider', service_details['presiderName']))
            if service_details.get('preacherName'):
                service_lower_thirds.append(('Preacher', service_details['preacherName']))
            
            for label, content in service_lower_thirds:
                lower_third = create_lower_third(
                    reading_type=label,
                    reference=content,
                    liturgical_season=liturgical_season,
                    is_funeral=is_funeral,
                    branding=branding,
                    style=style
                )
                img_buffer = io.BytesIO()
                lower_third.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                safe_label = label.replace(' ', '_')
                zip_file.writestr(f"{date_folder_name}/service_details/{safe_label}.png", img_buffer.read())
            
            blank_template = create_blank_lower_third(
                date_str=date_str,
                is_funeral=is_funeral,
                liturgical_season=liturgical_season,
                style=style
            )
            img_buffer = io.BytesIO()
            blank_template.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            zip_file.writestr(f"{date_folder_name}/lower_thirds/BLANK_TEMPLATE.png", img_buffer.read())
            
            if extras.get('includeAnnouncements') and extras.get('announcements'):
                announcements = extras['announcements']
                for idx, announcement in enumerate(announcements, 1):
                    ann_img = create_announcement_slide(announcement, branding=branding, style=style)
                    img_buffer = io.BytesIO()
                    ann_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    ann_type = announcement.get('type', 'general')
                    ann_title = announcement.get('title', f'Announcement_{idx}')
                    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in ann_title)[:30].strip()
                    zip_file.writestr(f"{date_folder_name}/announcements/Announcement_{idx}_{safe_title}.png", img_buffer.read())
            
            if extras.get('includeServiceOrder') and extras.get('serviceOrderItems'):
                order_items = extras['serviceOrderItems']
                show_numbering = extras.get('showOrderNumbering', False)
                for idx, item_text in enumerate(order_items, 1):
                    if not item_text.strip():
                        continue
                    order_img = create_service_order_slide(
                        order_item=item_text,
                        liturgical_season=liturgical_season,
                        is_memorial=is_funeral,
                        show_number=show_numbering,
                        item_number=idx,
                        branding=branding
                    )
                    img_buffer = io.BytesIO()
                    order_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    safe_item = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item_text)[:40].strip()
                    zip_file.writestr(f"{date_folder_name}/service_order/Order_{idx:02d}_{safe_item}.png", img_buffer.read())
            
            if extras.get('includeCountdown') and extras.get('countdownTimes'):
                countdown_times = extras['countdownTimes']
                welcome_message = extras.get('countdownWelcome', '')
                service_time = extras.get('countdownServiceTime', '')
                for minutes in sorted(countdown_times, reverse=True):
                    countdown_img = create_countdown_slide(
                        minutes=minutes,
                        liturgical_season=liturgical_season,
                        is_memorial=is_funeral,
                        welcome_message=welcome_message if welcome_message else None,
                        service_time=service_time if service_time else None,
                        branding=branding,
                        style=style
                    )
                    img_buffer = io.BytesIO()
                    countdown_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    zip_file.writestr(f"{date_folder_name}/countdown/Countdown_{minutes:02d}min.png", img_buffer.read())
            
            # Generate custom title slide
            if extras.get('includeCustomTitleSlide') and extras.get('customTitleText'):
                custom_title_text = extras['customTitleText']
                custom_title_card = create_title_card(
                    custom_title_text,
                    liturgical_season=liturgical_season,
                    is_funeral=is_funeral,
                    branding=branding,
                    style=style
                )
                img_buffer = io.BytesIO()
                custom_title_card.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(f"{date_folder_name}/title_cards/Custom_Title_Card.png", img_buffer.read())
            
            # Generate custom lower thirds
            custom_lower_thirds_count = 0
            if extras.get('includeCustomLowerThirds') and extras.get('customLowerThirds'):
                custom_lts = extras['customLowerThirds']
                for idx, custom_lt in enumerate(custom_lts, 1):
                    label = custom_lt.get('label', '').strip()
                    content = custom_lt.get('content', '').strip()
                    if label or content:
                        lower_third = create_lower_third(
                            reading_type=label if label else 'Custom',
                            reference=content if content else '',
                            liturgical_season=liturgical_season,
                            is_funeral=is_funeral,
                            branding=branding,
                            style=style
                        )
                        img_buffer = io.BytesIO()
                        lower_third.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        safe_label = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in label)[:30].strip() if label else f'Custom_{idx}'
                        zip_file.writestr(f"{date_folder_name}/lower_thirds/Custom_{idx:02d}_{safe_label}.png", img_buffer.read())
                        custom_lower_thirds_count += 1
            
            summary_content = []
            summary_content.append(f"Service Preparation Package")
            summary_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_content.append("=" * 60)
            summary_content.append(f"Date: {formatted_date}")
            summary_content.append(f"Celebration: {liturgical_name}")
            summary_content.append(f"Service Type: {service_type.title()}")
            summary_content.append(f"Style: {style.replace('_', ' ').title()}")
            summary_content.append("")
            summary_content.append("Contents:")
            summary_content.append("- Title Card")
            if readings:
                summary_content.append(f"- Readings: {len(readings)} items")
            if service_lower_thirds:
                summary_content.append(f"- Service Details: {len(service_lower_thirds)} lower thirds")
            if extras.get('includeAnnouncements'):
                summary_content.append(f"- Announcements: {len(extras.get('announcements', []))} slides")
            if extras.get('includeServiceOrder'):
                summary_content.append(f"- Service Order: {len([i for i in extras.get('serviceOrderItems', []) if i.strip()])} slides")
            if extras.get('includeCountdown'):
                summary_content.append(f"- Countdown: {len(extras.get('countdownTimes', []))} slides")
            if extras.get('includeCustomTitleSlide') and extras.get('customTitleText'):
                summary_content.append("- Custom Title Card: 1 slide")
            if custom_lower_thirds_count > 0:
                summary_content.append(f"- Custom Lower Thirds: {custom_lower_thirds_count} slides")
            
            zip_file.writestr(f"{date_folder_name}/Package_Summary.txt", "\n".join(summary_content))
        
        zip_buffer.seek(0)
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            as_attachment=True,
            download_name=f"service_package_{date_folder_name}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate service package'
        }), 500

@app.route('/api/wizard_preview', methods=['POST'])
def wizard_preview():
    """Generate preview thumbnails for wizard review step"""
    try:
        data = request.get_json()
        
        date_str = data.get('date')
        service_type = data.get('serviceType', 'eucharist')
        service_details = data.get('serviceDetails', {})
        readings = data.get('readings', {})
        style = data.get('style', 'classic')
        liturgical_override = data.get('liturgicalOverride', '')
        
        if not date_str:
            return jsonify({'success': False, 'error': 'No date provided'}), 400
        
        branding = load_branding_config()
        calendar_instance = WebLiturgicalCalendar()
        
        selected_date = datetime.fromisoformat(date_str)
        
        is_funeral = service_type == 'funeral'
        liturgical_season = liturgical_override if liturgical_override else None
        
        previews = []
        
        liturgical_info = calendar_instance.get_liturgical_info(selected_date.date())
        
        # Get liturgical name - prefer feast day, then proper Sunday name, then API
        if liturgical_info.get('feast_day'):
            liturgical_name = liturgical_info['feast_day']
        elif liturgical_info.get('is_sunday'):
            liturgical_name = calendar_instance.get_sunday_name(selected_date)
        else:
            readings_data = calendar_instance.liturgy_fetcher.fetch_daily_readings(selected_date)
            liturgical_name = readings_data.get('celebration', 'Sunday Service') if readings_data else 'Sunday Service'
        
        formatted_date = selected_date.strftime("%B %d, %Y")
        
        # Format title based on service type
        if service_type == 'eucharist':
            title_text = f"Holy Eucharist for the\n{liturgical_name}\n{formatted_date}"
        elif service_type == 'evensong':
            title_text = f"Evensong for the\n{liturgical_name}\n{formatted_date}"
        elif service_type == 'funeral':
            title_text = f"Funeral Service\n{formatted_date}"
        elif service_type == 'concert':
            title_text = f"Concert\n{formatted_date}"
        else:
            title_text = f"{liturgical_name}\n{formatted_date}"
        
        title_card = create_title_card(
            title_text,
            liturgical_season=liturgical_season,
            is_funeral=is_funeral,
            branding=branding,
            style=style
        )
        img_buffer = io.BytesIO()
        title_card.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        previews.append({'name': 'Title Card', 'image': f'data:image/png;base64,{img_b64}', 'category': 'title_cards'})
        
        if readings:
            for reading_key in ['first_reading', 'psalm', 'second_reading', 'gospel']:
                if reading_key in readings and readings[reading_key]:
                    reading_data = readings[reading_key]
                    reference = reading_data.get('reference', '')
                    reading_name = reading_key.replace('_', ' ').title()
                    
                    lower_third = create_lower_third(
                        reading_type=reading_name,
                        reference=reference,
                        liturgical_season=liturgical_season,
                        is_funeral=is_funeral,
                        branding=branding,
                        style=style
                    )
                    img_buffer = io.BytesIO()
                    lower_third.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                    previews.append({'name': reading_name, 'image': f'data:image/png;base64,{img_b64}', 'category': 'readings'})
        
        service_items = []
        if service_details.get('preludeTitle'):
            service_items.append(('Prelude', service_details['preludeTitle']))
        if service_details.get('openingHymn'):
            service_items.append(('Opening Hymn', service_details['openingHymn']))
        if service_details.get('closingHymn'):
            service_items.append(('Closing Hymn', service_details['closingHymn']))
        
        for label, content in service_items[:3]:
            lower_third = create_lower_third(
                reading_type=label,
                reference=content,
                liturgical_season=liturgical_season,
                is_funeral=is_funeral,
                branding=branding,
                style=style
            )
            img_buffer = io.BytesIO()
            lower_third.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_b64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            previews.append({'name': label, 'image': f'data:image/png;base64,{img_b64}', 'category': 'service_details'})
        
        return jsonify({
            'success': True,
            'previews': previews
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate previews'
        }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)