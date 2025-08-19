#!/usr/bin/env python3
"""
Deployment entry point for the liturgical calendar application.
This is a fallback entry point specifically for deployment environments.
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from web_calendar import app
    
    if __name__ == "__main__":
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        print(f"Starting Episcopal Liturgical Calendar on {host}:{port}")
        app.run(host=host, port=port, debug=False)
        
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Startup error: {e}")
    sys.exit(1)