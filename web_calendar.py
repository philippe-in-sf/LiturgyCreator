#!/usr/bin/env python3
"""
Web-based Interactive Liturgical Calendar
Episcopal Church Calendar with Revised Common Lectionary integration
"""

from flask import Flask, render_template, jsonify, request, send_file
import calendar
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import zipfile
import io
import textwrap
from liturgy_fetcher import LiturgyFetcher
from scripture_parser import ScriptureParser

app = Flask(__name__)

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
            if date_obj.month < 12:
                return "C"
            else:
                return "A"
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
        elif month in [11] and day >= 27:
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
                    # Format text with word wrapping at 50 characters
                    formatted_text = textwrap.fill(raw_text, width=50, break_long_words=False, break_on_hyphens=False)
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
            
            # Create service details file if provided
            if service_details:
                service_content = []
                service_content.append("Service Details")
                service_content.append("=" * 50)
                service_content.append("")
                
                # Hymns & Music
                if any(service_details.get(key) for key in ['openingHymn', 'sequenceHymn', 'communionMotet', 'closingHymn']):
                    service_content.append("HYMNS & MUSIC")
                    service_content.append("-" * 20)
                    if service_details.get('openingHymn'):
                        service_content.append(f"Opening Hymn: {service_details['openingHymn']}")
                    if service_details.get('sequenceHymn'):
                        service_content.append(f"Sequence Hymn: {service_details['sequenceHymn']}")
                    if service_details.get('communionMotet'):
                        service_content.append(f"Communion Motet: {service_details['communionMotet']}")
                    if service_details.get('closingHymn'):
                        service_content.append(f"Closing Hymn: {service_details['closingHymn']}")
                    service_content.append("")
                
                # Musicians
                if any(service_details.get(key) for key in ['organistName', 'preludeTitle', 'preludeComposer', 'postludeTitle', 'postludeComposer']):
                    service_content.append("MUSICIANS")
                    service_content.append("-" * 20)
                    if service_details.get('organistName'):
                        service_content.append(f"Organist: {service_details['organistName']}")
                    if service_details.get('preludeTitle') or service_details.get('preludeComposer'):
                        prelude = f"Prelude: {service_details.get('preludeTitle', '')} by {service_details.get('preludeComposer', '')}".strip(' by')
                        service_content.append(prelude)
                    if service_details.get('postludeTitle') or service_details.get('postludeComposer'):
                        postlude = f"Postlude: {service_details.get('postludeTitle', '')} by {service_details.get('postludeComposer', '')}".strip(' by')
                        service_content.append(postlude)
                    service_content.append("")
                
                # Clergy
                if any(service_details.get(key) for key in ['preacherName', 'presiderName']):
                    service_content.append("CLERGY")
                    service_content.append("-" * 20)
                    if service_details.get('preacherName'):
                        service_content.append(f"Preacher: {service_details['preacherName']}")
                    if service_details.get('presiderName'):
                        service_content.append(f"Presider: {service_details['presiderName']}")
                    service_content.append("")
                
                service_content.append(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                service_file_content = "\n".join(service_content)
                zip_file.writestr(f"{date_folder_name}/Service Details.txt", service_file_content)
            
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

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)