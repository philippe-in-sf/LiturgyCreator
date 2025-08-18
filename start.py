#!/usr/bin/env python3
"""
Universal start script for deployment environments
This serves as a fallback entry point that handles various deployment scenarios
"""

import os
import sys

def main():
    """Universal entry point for all deployment platforms"""
    try:
        # Import and run the web calendar application
        from web_calendar import app
        
        # Get port from environment or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        # Production deployment configuration
        debug_mode = False
        if os.environ.get('ENVIRONMENT') == 'development':
            debug_mode = True
            
        print(f"🕊️ Liturgical Calendar Web Application")
        print(f"🌐 Starting on 0.0.0.0:{port}")
        print(f"📅 Episcopal Church Daily Readings")
        print(f"🔧 Mode: {'Development' if debug_mode else 'Production'}")
        
        # Start the Flask application
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()