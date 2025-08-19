#!/usr/bin/env python3
"""
Entry point for running the liturgical calendar web application as a module.
This allows the app to be run with: python -m web_calendar
"""

import os
from web_calendar import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"Starting liturgical calendar web application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)