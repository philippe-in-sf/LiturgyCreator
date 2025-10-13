#!/usr/bin/env python3
"""
Web-based Interactive Liturgical Calendar
Episcopal Church Calendar with Revised Common Lectionary integration
Version: 1.9 - OBS Scene Generation
"""

from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
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
from functools import wraps
import uuid
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

# Get access code from environment
ACCESS_CODE = os.environ.get('ACCESS_CODE', '3501')

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            'advent': '#663399',      # Purple
            'christmas': '#FFFFFF',   # White
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
                return "A"
            else:
                return "C"
        elif date_obj.year == 2024:
            return "C"
        elif date_obj.year == 2026:
            return "A"
        else:
            cycle_year = (date_obj.year - 2022) % 3
            return ['A', 'B', 'C'][cycle_year]
            
    def get_liturgical_season(self, date_obj: datetime) -> str:
        """Determine the current liturgical season"""
        month = date_obj.month
        day = date_obj.day
        
        if month == 12 and day >= 25:
            return "Christmas Season"
        elif month == 1 and day <= 6:
            return "Christmas Season"
        elif month == 1 and day > 6:
            return "Season after Epiphany"
        elif month in [2, 3, 4]:
            return "Lenten Season / Easter Season"
        elif month in [5, 6]:
            return "Easter Season"
        elif (month == 11 and day >= 27) or (month == 12 and day < 25):
            return "Advent Season"
        else:
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
            'Lenten Season / Easter Season': 'lent',
            'Easter Season': 'easter',
            'Season after Pentecost': 'ordinary'
        }
        
        color = color_map.get(season, 'default')
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
        feast_days = {
            (1, 1): "New Year's Day",
            (1, 6): "Epiphany",
            (7, 4): "Independence Day",
            (8, 15): "St Mary, the Virgin",
            (9, 29): "St Michael and All Angels",
            (11, 1): "All Saints' Day",
            (11, 2): "All Souls' Day",
            (12, 25): "Christmas Day",
            (12, 26): "St Stephen, Deacon and Martyr"
        }
        
        # Use explicit key lookup to avoid type issues
        key = (month, day)
        if key in feast_days:
            return feast_days[key]
        return None
        
    def get_sunday_name(self, date_obj: datetime) -> str:
        """Get the proper name for Sunday in the liturgical calendar"""
        season = self.get_liturgical_season(date_obj)
        
        if "Pentecost" in season:
            week_of_year = date_obj.isocalendar()[1]
            if week_of_year >= 20 and week_of_year <= 45:
                proper_num = week_of_year - 19
                return f"Proper {proper_num} (Sunday after Pentecost)"
                
        return f"Sunday in {season}"
        
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
                    if liturgical_info['is_sunday']:
                        celebration = self.get_sunday_name(datetime.combine(cell_date, datetime.min.time()))
                    elif liturgical_info['feast_day']:
                        celebration = liturgical_info['feast_day']
                    
                    week_info.append({
                        'day': day,
                        'date': cell_date.isoformat(),
                        'is_today': cell_date == today,
                        'liturgical_info': liturgical_info,
                        'celebration': celebration
                    })
            
            calendar_info['weeks'].append(week_info)
            
        return calendar_info
        
    def get_readings_for_date(self, date_str: str) -> Dict[str, Any]:
        """Get readings for a specific date in OBS-compatible format"""
        try:
            # Parse date
            selected_date = datetime.fromisoformat(date_str)
            
            # Check if it's a Sunday or feast day
            liturgical_info = self.get_liturgical_info(selected_date.date())
            
            if not (liturgical_info['is_sunday'] or liturgical_info['feast_day']):
                return {}
            
            # Fetch readings
            readings_data = self.liturgy_fetcher.fetch_daily_readings(selected_date)
            
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        code = request.form.get('code', '')
        if code == ACCESS_CODE:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid access code')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main calendar page"""
    return render_template('calendar.html')

@app.route('/api/calendar/<int:year>/<int:month>')
@login_required
def get_calendar(year, month):
    """API endpoint to get calendar data"""
    try:
        calendar_data = web_calendar.get_calendar_data(year, month)
        return jsonify(calendar_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/readings/<date_str>')
@login_required
def get_readings(date_str):
    """API endpoint to get readings for a specific date"""
    try:
        # Parse date
        selected_date = datetime.fromisoformat(date_str)
        
        # Check if it's a Sunday or feast day
        liturgical_info = web_calendar.get_liturgical_info(selected_date.date())
        
        if not (liturgical_info['is_sunday'] or liturgical_info['feast_day']):
            return jsonify({
                'has_readings': False,
                'message': 'No special readings for this date. Weekday readings follow the daily lectionary.',
                'liturgical_info': liturgical_info
            })
        
        # Fetch readings
        readings_data = web_calendar.liturgy_fetcher.fetch_daily_readings(selected_date)
        
        if not readings_data:
            return jsonify({
                'has_readings': False,
                'message': 'Unable to load readings for this date.',
                'liturgical_info': liturgical_info
            })
        
        # Parse readings
        parsed_readings = web_calendar.scripture_parser.parse_readings(readings_data)
        
        return jsonify({
            'has_readings': True,
            'date': date_str,
            'liturgical_info': liturgical_info,
            'celebration': readings_data.get('celebration', 'Unknown'),
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

@app.route('/api/service_details', methods=['POST'])
def save_service_details():
    """API endpoint to save service details for a specific date"""
    try:
        data = request.get_json()
        date_str = data.get('date')
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
        
        # Save the new details
        service_data[date_str] = details
        
        try:
            with open(details_file, 'w') as f:
                json.dump(service_data, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': f'Service details saved for {date_str}'
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
    """API endpoint to get service details for a specific date"""
    try:
        import json
        import os
        
        details_file = 'service_details.json'
        
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r') as f:
                    service_data = json.load(f)
                    details = service_data.get(date_str, {})
                    
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
                
                if service_details.get('preludeComposer'):
                    formatted_composer = textwrap.fill(service_details['preludeComposer'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Prelude Composer.txt", formatted_composer)
                
                if service_details.get('postludeTitle'):
                    formatted_postlude = textwrap.fill(service_details['postludeTitle'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Postlude Title.txt", formatted_postlude)
                
                if service_details.get('postludeComposer'):
                    formatted_composer = textwrap.fill(service_details['postludeComposer'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/Postlude Composer.txt", formatted_composer)
                
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

def get_liturgical_season_colors(date_str: Optional[str] = None) -> Dict[str, tuple]:
    """Get liturgical season colors for lower third graphics"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    month = date_obj.month
    day = date_obj.day
    
    # Determine liturgical season
    season = 'ordinary'  # default
    
    if month == 12 and day >= 25:
        season = 'christmas'
    elif month == 1 and day <= 6:
        season = 'christmas'
    elif month == 1 and day > 6:
        season = 'epiphany'
    elif month in [2, 3] or (month == 4 and day < 15):
        # Rough Lent/Easter season (needs refinement for actual Easter dates)
        season = 'lent'
    elif month in [4, 5, 6] and (month > 4 or day >= 15):
        season = 'easter'
    elif (month == 11 and day >= 27) or (month == 12 and day < 25):
        season = 'advent'
    else:
        season = 'ordinary'
    
    # Color mapping with RGBA tuples (R, G, B, A)
    color_schemes = {
        'advent': {
            'background': (102, 51, 153, 230),   # Purple with opacity
            'accent': (102, 51, 153, 255),       # Purple solid
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        },
        'christmas': {
            'background': (255, 255, 255, 230),  # White with opacity
            'accent': (212, 175, 55, 255),       # Gold
            'title': (102, 51, 153, 255),        # Purple
            'text': (60, 60, 60, 255)            # Dark gray
        },
        'epiphany': {
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
        'ordinary': {
            'background': (0, 128, 0, 230),      # Green with opacity
            'accent': (34, 139, 34, 255),        # Forest green
            'title': (255, 255, 255, 255),       # White
            'text': (241, 241, 241, 255)         # Light gray
        }
    }
    
    return color_schemes.get(season, color_schemes['ordinary'])

def create_lower_third(reading_type: str, reference: str, date_str: Optional[str] = None, width: int = 1920, height: int = 1080) -> Image.Image:
    """Create a lower third graphic for broadcast use with liturgical season colors"""
    # Create image with transparent background (RGBA mode)
    img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Determine liturgical season colors
    liturgical_colors = get_liturgical_season_colors(date_str)
    
    # Try to load fonts, fallback to default if not available
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        ref_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        ref_font = ImageFont.load_default()
    
    # Format reading type (remove underscores, title case)
    formatted_type = reading_type.replace('_', ' ').title()
    
    # Calculate text dimensions to determine background height
    title_bbox = draw.textbbox((0, 0), formatted_type, font=title_font)
    ref_bbox = draw.textbbox((0, 0), reference, font=ref_font)
    
    # Calculate heights
    title_height = title_bbox[3] - title_bbox[1]
    ref_height = ref_bbox[3] - ref_bbox[1]
    
    # Padding values
    top_padding = 40
    text_spacing = 20
    bottom_padding = 40
    
    # Calculate total background height needed
    background_height = top_padding + title_height + text_spacing + ref_height + bottom_padding
    
    # Position lower third lower on screen (at 5/6 of the image height, lowered by 50% from original 2/3)
    lower_third_start = int(height * 5 / 6)
    background_end = lower_third_start + background_height
    
    # Draw semi-transparent background with liturgical season color
    draw.rectangle(
        [0, lower_third_start, width, background_end],
        fill=liturgical_colors['background']
    )
    
    # Draw accent bar on left side with liturgical season accent color
    draw.rectangle(
        [0, lower_third_start, 20, background_end],
        fill=liturgical_colors['accent']
    )
    
    # Logo space (reserved for logo to be added later)
    logo_space = 220  # Space reserved on left for logo
    text_indent = logo_space + 40  # Text starts after logo space plus padding
    
    # Draw reading type (title) - indented to leave room for logo
    title_y = lower_third_start + top_padding
    draw.text((text_indent, title_y), formatted_type, fill=liturgical_colors['title'], font=title_font)
    
    # Draw reference (below title)
    ref_y = title_y + title_height + text_spacing
    draw.text((text_indent, ref_y), reference, fill=liturgical_colors['text'], font=ref_font)
    
    return img

def generate_obs_scene_collection(readings: dict, service_details: dict, date_str: str) -> dict:
    """
    Generate an OBS scene collection JSON structure
    that references the exported Worship folder assets
    """
    sources = []
    scenes = []
    source_counter = 1
    
    # Helper function to create a text source definition
    def create_text_source_def(name: str, file_path: str):
        source_uuid = str(uuid.uuid4())
        source = {
            "id": "text_gdiplus_v2",
            "name": name,
            "uuid": source_uuid,
            "versioned_id": "text_gdiplus_v2",
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
            "flags": 0,
            "sync": 0,
            "filters": []
        }
        return source, source_uuid
    
    # Helper function to create an image source definition
    def create_image_source_def(name: str, file_path: str):
        source_uuid = str(uuid.uuid4())
        source = {
            "id": "image_source",
            "name": name,
            "uuid": source_uuid,
            "versioned_id": "image_source",
            "settings": {
                "file": file_path,
                "unload": False
            },
            "flags": 0,
            "sync": 0,
            "filters": []
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
    
    # Create sources and scenes for each scripture reading
    for reading_type, reading_data in readings.items():
        base_name = reading_type.replace('_', ' ').title()
        
        # Lower third image source and scene
        img_source, img_uuid = create_image_source_def(
            f"{base_name} Graphic",
            f"Worship/lower_thirds/{base_name}.png"
        )
        sources.append(img_source)
        
        scene = {
            "id": len(scenes) + 1,
            "name": f"{base_name} - Lower Third",
            "items": [
                create_scene_item(img_uuid, f"{base_name} Graphic", 0, 0, source_counter)
            ]
        }
        source_counter += 1
        scenes.append(scene)
        
        # Text sources and scene
        ref_source, ref_uuid = create_text_source_def(
            f"{base_name} Reference",
            f"Worship/readings/{base_name} Reference.txt"
        )
        sources.append(ref_source)
        
        text_source, text_uuid = create_text_source_def(
            f"{base_name} Text",
            f"Worship/readings/{base_name}.txt"
        )
        sources.append(text_source)
        
        text_scene = {
            "id": len(scenes) + 1,
            "name": f"{base_name} - Full Text",
            "items": [
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
                f"Worship/lower_thirds/{field_label}.png"
            )
            sources.append(hymn_img_source)
            
            hymn_scene = {
                "id": len(scenes) + 1,
                "name": f"{field_label} - Lower Third",
                "items": [
                    create_scene_item(hymn_img_uuid, f"{field_label} Graphic", 0, 0, source_counter)
                ]
            }
            source_counter += 1
            scenes.append(hymn_scene)
            
            # Text for hymn
            hymn_title_source, hymn_title_uuid = create_text_source_def(
                f"{field_label} Title",
                f"Worship/service_details/{field_label}.txt"
            )
            sources.append(hymn_title_source)
            
            hymn_text_source, hymn_text_uuid = create_text_source_def(
                f"{field_label} Full Text",
                f"Worship/service_details/{field_label} Text.txt"
            )
            sources.append(hymn_text_source)
            
            hymn_text_scene = {
                "id": len(scenes) + 1,
                "name": f"{field_label} - Text",
                "items": [
                    create_scene_item(hymn_title_uuid, f"{field_label} Title", 100, 100, source_counter),
                    create_scene_item(hymn_text_uuid, f"{field_label} Full Text", 100, 200, source_counter + 1)
                ]
            }
            source_counter += 2
            scenes.append(hymn_text_scene)
    
    # Create the complete scene collection structure
    scene_collection = {
        "name": f"Worship Service {date_str}",
        "current_scene": scenes[0]["name"] if scenes else "",
        "scenes": scenes,
        "sources": sources,
        "transition_duration": 300,
        "current_transition": "Fade"
    }
    
    return scene_collection

@app.route('/api/export_all', methods=['POST'])
@login_required
def export_all():
    """Combined export: readings text files + lower third graphics in one ZIP"""
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
        date_folder_name = "Worship"
        
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
                
                if service_details.get('preludeTitle'):
                    formatted_prelude = textwrap.fill(service_details['preludeTitle'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Prelude Title.txt", formatted_prelude)
                
                if service_details.get('preludeComposer'):
                    formatted_composer = textwrap.fill(service_details['preludeComposer'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Prelude Composer.txt", formatted_composer)
                
                if service_details.get('postludeTitle'):
                    formatted_postlude = textwrap.fill(service_details['postludeTitle'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Postlude Title.txt", formatted_postlude)
                
                if service_details.get('postludeComposer'):
                    formatted_composer = textwrap.fill(service_details['postludeComposer'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Postlude Composer.txt", formatted_composer)
                
                # Individual clergy files
                if service_details.get('preacherName'):
                    formatted_preacher = textwrap.fill(service_details['preacherName'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Preacher.txt", formatted_preacher)
                
                if service_details.get('presiderName'):
                    formatted_presider = textwrap.fill(service_details['presiderName'], width=50, break_long_words=False, break_on_hyphens=False)
                    zip_file.writestr(f"{date_folder_name}/service_details/Presider.txt", formatted_presider)
            
            # ===== PART 2: Generate lower third graphics =====
            # Create lower third graphic for each reading
            for reading_type, reading_data in readings.items():
                reference = reading_data.get('reference', 'No reference')
                
                # Generate lower third image with liturgical season colors
                img = create_lower_third(reading_type, reference, date_str)
                
                # Save image to buffer
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Add to ZIP with proper filename
                filename = f"{reading_type.replace('_', ' ').title()}.png"
                filepath = f"{date_folder_name}/lower_thirds/{filename}"
                zip_file.writestr(filepath, img_buffer.read())
            
            # Create lower third graphics for hymns and music
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
                if hymn_value:  # Only create graphic if field has content
                    # Generate lower third image with liturgical season colors
                    img = create_lower_third(field_label, hymn_value, date_str)
                    
                    # Save image to buffer
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # Add to ZIP with proper filename
                    filename = f"{field_label}.png"
                    filepath = f"{date_folder_name}/lower_thirds/{filename}"
                    zip_file.writestr(filepath, img_buffer.read())
            
            # ===== PART 3: Generate OBS Scene Collection =====
            obs_collection = generate_obs_scene_collection(readings, service_details, date_str)
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
@login_required
def generate_lower_thirds():
    """Generate lower third graphics for broadcast use"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        
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
                img = create_lower_third(reading_type, reference, date_str)
                
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
                'closingHymn': 'Closing Hymn'
            }
            
            for field_key, field_label in hymn_fields.items():
                hymn_value = service_details.get(field_key, '').strip()
                if hymn_value:  # Only create graphic if field has content
                    # Generate lower third image with liturgical season colors
                    img = create_lower_third(field_label, hymn_value, date_str)
                    
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

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)