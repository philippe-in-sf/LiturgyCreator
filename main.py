#!/usr/bin/env python3
"""
Main entry point for Replit deployment
"""
import os
from web_calendar import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)