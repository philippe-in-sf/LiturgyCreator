#!/bin/bash
# Deployment startup script

# Set default port if not provided
export PORT=${PORT:-5000}

# Start the web application
python3 app.py