#!/usr/bin/env python3
"""
Main entry point for Episcopal Liturgical Calendar web application.
Optimized for Cloud Run deployment with proper error handling.
"""

import os
import sys

def main():
    try:
        # Import the Flask app
        from web_calendar import app
        
        # Get port from environment (Cloud Run sets this)
        port = int(os.environ.get("PORT", 5000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"Starting Episcopal Liturgical Calendar on {host}:{port}")
        
        # Run in production mode for deployment
        app.run(
            host=host, 
            port=port, 
            debug=False,
            threaded=True
        )
        
    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()