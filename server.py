#!/usr/bin/env python3
"""
Production server entry point for Replit deployment
This file serves as the primary entry point for the liturgical calendar web application
"""

import os
from web_calendar import app

# Production configuration
if __name__ == "__main__":
    # Get port from environment variable (Replit sets this automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Production deployment should not use debug mode
    debug_mode = False
    
    print(f"🕊️ Liturgical Calendar Web Application")
    print(f"🌐 Starting server on 0.0.0.0:{port}")
    print(f"📅 Episcopal Church liturgical calendar with daily readings")
    print(f"🔧 Production mode (debug={debug_mode})")
    
    # Start the Flask application
    # Bind to 0.0.0.0 to accept external connections for deployment
    app.run(host='0.0.0.0', port=port, debug=debug_mode)