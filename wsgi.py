#!/usr/bin/env python3
"""
WSGI entry point for deployment platforms
Compatible with Gunicorn, uWSGI, and other WSGI servers
"""

import os
from web_calendar import app

# Expose the Flask app for WSGI servers
application = app

if __name__ == "__main__":
    # For direct execution (development)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)