#!/usr/bin/env python3
"""
Main application entry point for deployment
Serves the liturgical calendar web application
"""

import os
from web_calendar import app

def main():
    """Main entry point for deployment"""
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Determine if we're in debug mode
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting Liturgical Calendar Web Application on port {port}")
    print(f"Debug mode: {debug}")
    
    # Run the Flask application
    # For deployment, we bind to 0.0.0.0 to accept external connections
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()