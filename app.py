#!/usr/bin/env python3
"""
Main application entry point for deployment
Serves the liturgical calendar web application
"""

import os
from web_calendar import app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask application
    # For deployment, we bind to 0.0.0.0 to accept external connections
    app.run(host='0.0.0.0', port=port, debug=False)