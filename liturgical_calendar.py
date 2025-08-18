#!/usr/bin/env python3
"""
Interactive Liturgical Calendar Visualization
Episcopal Church Calendar with Revised Common Lectionary integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import json
from liturgy_fetcher import LiturgyFetcher
from scripture_parser import ScriptureParser

class LiturgicalCalendar:
    """Interactive liturgical calendar with Episcopal Church seasons and readings"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Episcopal Liturgical Calendar - Year C")
        self.root.geometry("1200x800")
        
        # Initialize liturgy components
        self.liturgy_fetcher = LiturgyFetcher()
        self.scripture_parser = ScriptureParser()
        
        # Current date tracking
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        
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
        
        # Liturgical data cache
        self.readings_cache = {}
        
        self.setup_ui()
        self.update_calendar()
        
    def setup_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title and navigation
        self.setup_header(main_frame)
        
        # Calendar grid
        self.setup_calendar_grid(main_frame)
        
        # Reading details panel
        self.setup_details_panel(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
        
    def setup_header(self, parent):
        """Setup calendar header with navigation"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Navigation buttons
        ttk.Button(header_frame, text="◀ Prev", command=self.prev_month).grid(row=0, column=0, padx=(0, 10))
        
        # Month/Year label
        self.month_label = ttk.Label(header_frame, font=('Arial', 16, 'bold'))
        self.month_label.grid(row=0, column=1)
        
        ttk.Button(header_frame, text="Next ▶", command=self.next_month).grid(row=0, column=2, padx=(10, 0))
        
        # Liturgical year info
        liturgical_frame = ttk.Frame(header_frame)
        liturgical_frame.grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        self.liturgical_year_label = ttk.Label(liturgical_frame, font=('Arial', 12))
        self.liturgical_year_label.pack()
        
        # Today button
        ttk.Button(header_frame, text="Today", command=self.go_to_today).grid(row=0, column=3, padx=(10, 0))
        
    def setup_calendar_grid(self, parent):
        """Setup the calendar grid"""
        calendar_frame = ttk.LabelFrame(parent, text="Calendar", padding="5")
        calendar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Days of week header
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            label = ttk.Label(calendar_frame, text=day, font=('Arial', 10, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1, sticky=(tk.W, tk.E))
        
        # Calendar cells
        self.calendar_cells = {}
        for week in range(6):  # 6 weeks max for any month
            for day in range(7):
                cell = tk.Button(
                    calendar_frame,
                    width=12,
                    height=3,
                    font=('Arial', 9),
                    relief='raised',
                    bd=1,
                    command=lambda w=week, d=day: self.on_date_click(w, d)
                )
                cell.grid(row=week+1, column=day, padx=1, pady=1, sticky=(tk.W, tk.E))
                self.calendar_cells[(week, day)] = cell
                
        # Configure column weights
        for i in range(7):
            calendar_frame.columnconfigure(i, weight=1)
            
    def setup_details_panel(self, parent):
        """Setup the reading details panel"""
        details_frame = ttk.LabelFrame(parent, text="Liturgical Details", padding="5")
        details_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(1, weight=1)
        
        # Date and celebration info
        self.date_info_label = ttk.Label(details_frame, font=('Arial', 14, 'bold'))
        self.date_info_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Scrollable text for readings
        text_frame = ttk.Frame(details_frame)
        text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.readings_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            padx=10,
            pady=10
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.readings_text.yview)
        self.readings_text.configure(yscrollcommand=scrollbar.set)
        
        self.readings_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Action buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Load Reading", command=self.load_selected_reading).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Send to OBS", command=self.send_to_obs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export", command=self.export_reading).pack(side=tk.LEFT, padx=5)
        
    def setup_status_bar(self, parent):
        """Setup status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def update_calendar(self):
        """Update the calendar display"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update month label
        month_name = calendar.month_name[month]
        self.month_label.config(text=f"{month_name} {year}")
        
        # Update liturgical year info
        liturgical_year = self.get_liturgical_year(self.current_date)
        season = self.get_liturgical_season(self.current_date)
        self.liturgical_year_label.config(text=f"Liturgical Year {liturgical_year} • {season}")
        
        # Get calendar data
        cal = calendar.monthcalendar(year, month)
        
        # Clear all cells
        for cell in self.calendar_cells.values():
            cell.config(text="", bg='white', state='disabled')
            
        # Fill calendar cells
        today = datetime.now().date()
        
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                cell = self.calendar_cells[(week_num, day_num)]
                cell_date = date(year, month, day)
                
                # Determine liturgical info for this date
                liturgical_info = self.get_liturgical_info(cell_date)
                
                # Format cell text
                cell_text = str(day)
                if liturgical_info['is_sunday']:
                    cell_text += "\n(Sunday)"
                elif liturgical_info['feast_day']:
                    cell_text += f"\n{liturgical_info['feast_day'][:10]}..."
                    
                # Set cell color based on liturgical season/feast
                color = self.liturgical_colors.get(liturgical_info['color'], self.liturgical_colors['default'])
                
                # Highlight today
                if cell_date == today:
                    cell.config(
                        text=cell_text,
                        bg='yellow',
                        fg='black',
                        state='normal',
                        font=('Arial', 9, 'bold')
                    )
                # Highlight selected date
                elif cell_date == self.selected_date.date():
                    cell.config(
                        text=cell_text,
                        bg='lightblue',
                        fg='black',
                        state='normal',
                        font=('Arial', 9, 'bold')
                    )
                else:
                    # Text color based on background
                    text_color = 'white' if color in ['#663399', '#AA0000', '#000000'] else 'black'
                    cell.config(
                        text=cell_text,
                        bg=color,
                        fg=text_color,
                        state='normal',
                        font=('Arial', 9)
                    )
                
                # Store date for click handler
                cell.date = cell_date
                
    def get_liturgical_year(self, date_obj: datetime) -> str:
        """Determine the liturgical year (A, B, or C)"""
        # Liturgical year starts with First Sunday of Advent
        # Year C: 2024-2025 (ends November 2025)
        # Year A: 2025-2026 (starts Advent 2025)
        # Year B: 2026-2027
        
        if date_obj.year == 2025:
            if date_obj.month < 12:  # Before Advent 2025
                return "C"
            else:  # Advent 2025 starts Year A
                return "A"
        elif date_obj.year == 2024:
            return "C"
        elif date_obj.year == 2026:
            return "A"
        else:
            # Calculate based on cycle
            cycle_year = (date_obj.year - 2022) % 3
            return ['A', 'B', 'C'][cycle_year]
            
    def get_liturgical_season(self, date_obj: datetime) -> str:
        """Determine the current liturgical season"""
        month = date_obj.month
        day = date_obj.day
        
        # This is a simplified calculation
        # In production, you'd calculate based on Easter date
        
        if month == 12 and day >= 25:
            return "Christmas Season"
        elif month == 1 and day <= 6:
            return "Christmas Season"
        elif month == 1 and day > 6:
            return "Season after Epiphany"
        elif month in [2, 3, 4]:  # Rough Lent/Easter calculation
            return "Lenten Season / Easter Season"
        elif month in [5, 6]:
            return "Easter Season"
        elif month in [11] and day >= 27:
            return "Advent Season"
        else:
            return "Season after Pentecost"
            
    def get_liturgical_info(self, date_obj: date) -> Dict:
        """Get liturgical information for a specific date"""
        weekday = date_obj.weekday()  # 0 = Monday, 6 = Sunday
        is_sunday = (weekday == 6)
        
        # Determine liturgical color and any special feast
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
        
        # Check for special feast days
        feast_day = self.get_feast_day(date_obj)
        if feast_day:
            color = 'feast'
            
        return {
            'is_sunday': is_sunday,
            'color': color,
            'season': season,
            'feast_day': feast_day
        }
        
    def get_feast_day(self, date_obj: date) -> Optional[str]:
        """Check if date is a special feast day"""
        month = date_obj.month
        day = date_obj.day
        
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
        
        return feast_days.get((month, day))
        
    def on_date_click(self, week: int, day: int):
        """Handle date cell click"""
        cell = self.calendar_cells[(week, day)]
        if hasattr(cell, 'date'):
            self.selected_date = datetime.combine(cell.date, datetime.min.time())
            self.update_calendar()
            self.update_details()
            
    def update_details(self):
        """Update the details panel with selected date information"""
        date_str = self.selected_date.strftime("%A, %B %d, %Y")
        liturgical_info = self.get_liturgical_info(self.selected_date.date())
        
        # Update date info
        celebration = liturgical_info['season']
        if liturgical_info['feast_day']:
            celebration = liturgical_info['feast_day']
        elif liturgical_info['is_sunday']:
            celebration = self.get_sunday_name(self.selected_date)
            
        self.date_info_label.config(text=f"{date_str}\n{celebration}")
        
        # Clear previous content
        self.readings_text.delete(1.0, tk.END)
        
        if liturgical_info['is_sunday'] or liturgical_info['feast_day']:
            self.readings_text.insert(tk.END, "Loading readings...\n")
            self.root.after(100, self.load_readings_async)
        else:
            self.readings_text.insert(tk.END, "No special readings for this date.\n")
            self.readings_text.insert(tk.END, "Weekday readings follow the daily lectionary.\n\n")
            self.readings_text.insert(tk.END, f"Liturgical Season: {liturgical_info['season']}\n")
            self.readings_text.insert(tk.END, f"Liturgical Color: {liturgical_info['color'].title()}")
            
    def get_sunday_name(self, date_obj: datetime) -> str:
        """Get the proper name for Sunday in the liturgical calendar"""
        # This is simplified - would need proper calculation for actual Sunday names
        season = self.get_liturgical_season(date_obj)
        
        if "Pentecost" in season:
            # Calculate which Sunday after Pentecost
            # This is a rough estimate
            week_of_year = date_obj.isocalendar()[1]
            if week_of_year >= 20 and week_of_year <= 45:
                proper_num = week_of_year - 19
                return f"Proper {proper_num} (Sunday after Pentecost)"
                
        return f"Sunday in {season}"
        
    def load_readings_async(self):
        """Load readings asynchronously to avoid UI freezing"""
        try:
            readings_data = self.liturgy_fetcher.fetch_daily_readings(self.selected_date)
            if readings_data:
                self.display_readings(readings_data)
            else:
                self.readings_text.delete(1.0, tk.END)
                self.readings_text.insert(tk.END, "Unable to load readings for this date.\n")
                self.readings_text.insert(tk.END, "Please check your internet connection.")
        except Exception as e:
            self.readings_text.delete(1.0, tk.END)
            self.readings_text.insert(tk.END, f"Error loading readings: {str(e)}")
            
    def display_readings(self, readings_data: Dict):
        """Display readings in the details panel"""
        self.readings_text.delete(1.0, tk.END)
        
        # Header
        celebration = readings_data.get('celebration', 'Unknown')
        source = readings_data.get('source', 'Unknown')
        liturgical_year = readings_data.get('liturgical_year', 'Unknown')
        
        self.readings_text.insert(tk.END, f"📅 {celebration}\n")
        self.readings_text.insert(tk.END, f"🔄 {liturgical_year}\n")
        self.readings_text.insert(tk.END, f"📖 Source: {source}\n")
        self.readings_text.insert(tk.END, "-" * 50 + "\n\n")
        
        # Parse readings
        parsed_readings = self.scripture_parser.parse_readings(readings_data)
        
        if not parsed_readings:
            self.readings_text.insert(tk.END, "No readings available for this date.")
            return
            
        # Display each reading
        reading_order = ['first_reading', 'psalm', 'second_reading', 'gospel', 'collect']
        
        for reading_type in reading_order:
            if reading_type in parsed_readings:
                reading_data = parsed_readings[reading_type]
                
                # Reading title
                title = reading_type.replace('_', ' ').title()
                self.readings_text.insert(tk.END, f"📖 {title}\n", 'heading')
                
                # Reference
                reference = reading_data.get('reference', 'N/A')
                self.readings_text.insert(tk.END, f"Reference: {reference}\n\n")
                
                # Text (truncated for display)
                text = reading_data.get('text', 'N/A')
                if len(text) > 300:
                    text = text[:300] + "..."
                self.readings_text.insert(tk.END, f"{text}\n\n")
                self.readings_text.insert(tk.END, "-" * 30 + "\n\n")
                
        # Configure text tags
        self.readings_text.tag_configure('heading', font=('Arial', 11, 'bold'))
        
    def load_selected_reading(self):
        """Load the full reading for the selected date"""
        if not hasattr(self, 'selected_date'):
            messagebox.showwarning("No Date Selected", "Please select a date first.")
            return
            
        self.status_var.set("Loading readings...")
        self.root.update()
        
        try:
            readings_data = self.liturgy_fetcher.fetch_daily_readings(self.selected_date)
            if readings_data:
                self.display_readings(readings_data)
                self.status_var.set(f"Loaded readings for {self.selected_date.strftime('%B %d, %Y')}")
            else:
                self.status_var.set("Failed to load readings")
                messagebox.showerror("Error", "Unable to load readings for the selected date.")
        except Exception as e:
            self.status_var.set("Error loading readings")
            messagebox.showerror("Error", f"Error loading readings: {str(e)}")
            
    def send_to_obs(self):
        """Send readings to OBS (placeholder for future integration)"""
        messagebox.showinfo("OBS Integration", 
                          "This feature will integrate with your existing OBS automation.\n"
                          "The selected readings will be sent to your configured OBS text sources.")
        self.status_var.set("OBS integration coming soon...")
        
    def export_reading(self):
        """Export reading to file"""
        if not hasattr(self, 'selected_date'):
            messagebox.showwarning("No Date Selected", "Please select a date first.")
            return
            
        # This would implement file export functionality
        messagebox.showinfo("Export", "Export functionality coming soon...")
        
    def prev_month(self):
        """Navigate to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
        
    def next_month(self):
        """Navigate to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
        
    def go_to_today(self):
        """Navigate to current month"""
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.update_calendar()
        self.update_details()
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = LiturgicalCalendar()
    app.run()

if __name__ == "__main__":
    main()