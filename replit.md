# Overview

This project is a Daily Liturgical Scripture OBS Automation system that fetches **Episcopal Church liturgical readings** from The Lectionary Page (Revised Common Lectionary) and automatically updates text sources in OBS Studio via WebSocket connections. The system retrieves daily scripture readings based on the Episcopal liturgical calendar, parses them into a formatted structure, and displays them in configured OBS scenes for live streaming or recording purposes.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## API and Deployment Fixes (August 18, 2025)

### Readings API Resolution
- **Issue**: External liturgical APIs (Vanderbilt, lectionarypage.net) returning 403 Forbidden errors
- **Resolution**: Enhanced fallback system with priority order:
  1. Local readings database (primary)
  2. External APIs (secondary)  
  3. Closest Sunday readings (tertiary)
- **Coverage**: Added comprehensive Sunday readings for August 2025
- **User Preference**: Focus on Sunday readings rather than weekdays (per user request)

### Deployment Configuration Fixes
- **Issue**: Deployment failed due to undefined `$file` variable in run command
- **Resolution**: Created comprehensive deployment configuration:
  - `app.py`: Primary Flask application entry point with proper main() function
  - `wsgi.py`: WSGI-compatible entry point for production servers (Gunicorn, uWSGI)
  - `main.py`: Alternative entry point with enhanced logging and environment detection
  - `run.py`: Universal run script for deployment platforms with debug status
  - `Procfile`: Heroku-style process file specifying `python app.py` as web startup command
- **Entry Point**: Web calendar application (`web_calendar.py`) serves as the main web interface
- **Host Configuration**: All entry points configured to bind to `0.0.0.0` with PORT environment variable support
- **Environment Variables**: Support for `PORT`, `FLASK_DEBUG`, and `ENVIRONMENT` variables for deployment flexibility
- **Deployment Target**: Configured for Google Cloud Run via Replit deployment system

# System Architecture

## Core Components

The application follows a modular architecture with five main components:

### LiturgyFetcher Module
- **Purpose**: Handles fetching Episcopal liturgical calendar data and scripture readings from RCL sources
- **Design**: Uses a fallback system with multiple sources (The Lectionary Page and Vanderbilt Divinity Library)
- **Implementation**: Session-based HTTP client with web scraping capabilities using BeautifulSoup
- **Liturgical Calendar**: Follows the Revised Common Lectionary as adapted for Episcopal worship
- **Error Handling**: Graceful fallback between sources if primary source fails

### OBSController Module
- **Purpose**: Manages WebSocket connection and communication with OBS Studio
- **Design**: Uses obsws-python library for WebSocket protocol implementation
- **Configuration**: Supports configurable host, port, password, and scene mappings
- **Scene Management**: Maps scripture readings to specific OBS text sources and scenes

### ScriptureParser Module
- **Purpose**: Parses and formats liturgical readings for display
- **Design**: Handles scripture reference abbreviations and text formatting
- **Features**: Includes comprehensive book abbreviation mappings for consistent display
- **Output**: Structures readings into OBS-compatible text formats

### Main Application Controller
- **Purpose**: Orchestrates the entire automation workflow
- **Design**: Sequential execution pattern with error handling and logging
- **Configuration**: INI-file based configuration management
- **Logging**: Dual logging to file and console with structured format

### Interactive Liturgical Calendar
- **Purpose**: Provides visual calendar interface for browsing liturgical seasons and readings
- **Design**: Dual implementation with both desktop GUI (Tkinter) and web interface (Flask)
- **Features**: Month navigation, liturgical color coding, reading preview, OBS integration
- **Calendar Logic**: Episcopal liturgical year tracking (A/B/C cycle), season detection, feast day identification
- **Web Interface**: Responsive design with real-time reading loading and OBS automation integration

## Configuration Management

The system uses INI-based configuration files with sections for:
- OBS connection settings (host, port, password)
- Scene mappings (reading types to OBS sources)
- API preferences and fallback behavior

## Error Handling Strategy

- **Graceful Degradation**: Multiple API fallbacks ensure readings are retrieved
- **Connection Resilience**: OBS connection failures are logged but don't crash the system
- **Comprehensive Logging**: All operations are logged for debugging and monitoring

## Data Flow Architecture

1. **Fetch Phase**: Retrieve liturgical data from external APIs
2. **Parse Phase**: Structure and format scripture readings
3. **Connect Phase**: Establish WebSocket connection to OBS
4. **Update Phase**: Push formatted text to configured OBS sources

# External Dependencies

## Required Libraries
- **obsws-python**: WebSocket client for OBS Studio communication
- **requests**: HTTP client for API calls to liturgical services
- **configparser**: Configuration file management
- **logging**: Application logging and monitoring

## External APIs
- **The Lectionary Page (lectionarypage.net)**: Primary source for Episcopal RCL readings and calendar data
- **Vanderbilt Divinity Library RCL**: Fallback source for Revised Common Lectionary scripture readings
- **Web Scraping**: Uses BeautifulSoup for parsing HTML content from liturgical websites

## System Requirements
- **OBS Studio**: Must be running with WebSocket server enabled
- **Python 3.x**: Runtime environment for the automation script
- **Network Access**: Required for fetching liturgical data from external APIs

## Configuration Files
- **config.ini**: Contains OBS connection settings and scene mappings
- **liturgy_obs.log**: Application log file for monitoring and debugging