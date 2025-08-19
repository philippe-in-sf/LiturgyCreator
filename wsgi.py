"""
WSGI entry point for production deployment.
This file provides the WSGI application object for production servers.
"""

import os
from web_calendar import app

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# WSGI application object
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)