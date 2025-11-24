#!/usr/bin/env python3
"""
Trinity Church Streaming Design - macOS Launcher
Starts the Flask web server and opens the application in the default browser
"""

import os
import sys
import time
import webbrowser
import subprocess
import signal
from pathlib import Path

# Determine the application's resource path
if getattr(sys, 'frozen', False):
    # Running as compiled app bundle
    app_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(os.path.dirname(sys.executable)).parent / 'Resources'
else:
    # Running as script
    app_dir = Path(__file__).parent

# Change to app directory
os.chdir(app_dir)

# Set up environment
PORT = 5000
HOST = '127.0.0.1'
URL = f'http://{HOST}:{PORT}'

def start_server():
    """Start the Flask server"""
    print(f"Starting Trinity Church Streaming Design on {URL}")
    print("Press Ctrl+C to quit")
    
    # Import and run the Flask app
    sys.path.insert(0, str(app_dir))
    
    try:
        import web_calendar
        from werkzeug.serving import run_simple
        
        # Run the Flask app
        run_simple(HOST, PORT, web_calendar.app, 
                   use_reloader=False, 
                   use_debugger=False,
                   threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

def open_browser():
    """Open the default browser to the application URL"""
    time.sleep(1.5)  # Give server time to start
    print(f"Opening browser to {URL}")
    webbrowser.open(URL)

if __name__ == '__main__':
    # Open browser in background thread
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server (blocks until Ctrl+C)
    start_server()
