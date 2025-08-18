#!/usr/bin/env python3
"""
Universal run script for the liturgical calendar application
This serves as the main entry point that can be referenced in deployment configurations
"""

import os
import sys
from web_calendar import app

def main():
    """Main application entry point for deployment"""
    # Check if we're running in a deployment environment
    port = int(os.environ.get('PORT', 5000))
    
    # Disable debug mode for production deployments
    debug_mode = False
    if os.environ.get('ENVIRONMENT') == 'development':
        debug_mode = True
    
    print(f"🕊️ Starting Liturgical Calendar Web Application")
    print(f"📡 Server: 0.0.0.0:{port}")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🌐 Web calendar interface ready for access")
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

if __name__ == '__main__':
    main()