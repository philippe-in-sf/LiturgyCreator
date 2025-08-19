#!/usr/bin/env python3
"""
Simple entry point for Replit deployment
"""
import os
from web_calendar import app

def main():
    """Main entry point function"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()