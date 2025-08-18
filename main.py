#!/usr/bin/env python3
"""
Alternative main entry point for the liturgical calendar web application
This file serves as the primary entry point for deployment platforms
"""

import os
import sys
from web_calendar import app

def main():
    """Main application entry point"""
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # For production deployment, disable debug mode
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Liturgical Calendar Web Application on port {port}")
    print(f"Debug mode: {debug_mode}")
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

if __name__ == '__main__':
    main()