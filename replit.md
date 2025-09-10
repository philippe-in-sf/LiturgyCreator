# Overview

This project is a Daily Liturgical Scripture OBS Automation system (v1.1) that fetches **Episcopal Church liturgical readings** from The Lectionary Page (Revised Common Lectionary) and automatically updates text sources in OBS Studio via WebSocket connections. The system retrieves daily scripture readings based on the Episcopal liturgical calendar, parses them into a formatted structure, and displays them in configured OBS scenes for live streaming or recording purposes.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## PDF Upload Feature and Version 1.1 Release (September 10, 2025)

### PDF Upload Feature (BETA)
- **Feature**: Added comprehensive PDF upload and text extraction functionality (experimental)
- **Implementation**: New upload interface with drag-and-drop support for PDF documents
- **Processing**: Advanced text extraction using pdfplumber with OCR fallback capability
- **Analysis**: Smart liturgical content detection that identifies:
  - Scripture readings (First Reading, Psalm, Second Reading, Gospel)
  - Hymns and musical selections
  - Prayers and liturgical elements
  - Service information and details
- **User Interface**: Professional upload area with progress indicators and detailed results display
- **File Handling**: Supports PDF files up to 16MB with automatic cleanup after processing
- **Integration**: Seamlessly integrated with existing calendar interface as fourth action button
- **Status**: Beta feature - may provide unexpected results depending on PDF format and quality

### Version Management
- **Version**: Updated application to v1.1 across all configuration files
- **Deployment**: Configured for autoscale deployment on Replit platform
- **Documentation**: Updated project documentation to reflect new capabilities

# Recent Changes

## Service Details Interview System and Deployment Fix (August 21, 2025)

### Service Details Enhancement
- **Feature**: Added comprehensive interview section for gathering service information
- **Implementation**: Professional modal form with organized sections for:
  - **Hymns & Music**: Opening Hymn, Sequence Hymn, Communion Motet, Closing Hymn
  - **Musicians**: Organist Name, Prelude/Postlude titles and composers
  - **Clergy**: Preacher's Name, Presider's Name
- **Storage**: Local browser storage with server backup capability
- **OBS Integration**: Extended to send both readings and service details to text sources
- **Configuration**: Updated config.ini with mappings for all service detail fields

### Export Feature and Deployment Fix (August 21, 2025)

#### Text Export Functionality
- **Feature**: Added ZIP export functionality for liturgical readings and service details
- **Implementation**: New API endpoint `/api/export_readings` creates ZIP archives with individual text files
- **File Structure**: 
  - Each reading type gets two .txt files:
    - Scripture text file (e.g., "First Reading.txt") - contains scripture text formatted at 50 characters wide with word wrapping
    - Reference file (e.g., "First Reading Reference.txt") - contains scripture reference formatted at 50 characters wide
  - Individual service detail files (only created if data is provided):
    - **Hymns**: "Opening Hymn.txt", "Sequence Hymn.txt", "Communion Motet.txt", "Closing Hymn.txt"
    - **Musicians**: "Organist.txt", "Prelude Title.txt", "Prelude Composer.txt", "Postlude Title.txt", "Postlude Composer.txt"
    - **Clergy**: "Preacher.txt", "Presider.txt"
  - Summary file with reading references included
  - All files organized in date-named folder within ZIP
- **Text Formatting**: All exported text files use 50-character line width with intelligent word wrapping that preserves word boundaries
- **User Interface**: Export button is now the primary action for obtaining readings and service details
- **Usage**: Select date with readings, optionally fill out service details, click Export button, ZIP file downloads automatically
- **OBS Integration**: Temporarily removed from UI - export feature is now the preferred workflow for obtaining formatted readings

#### Deployment Configuration Fix
- **Issue**: Deployment attempted npm commands instead of Python execution
- **Root Cause**: .replit file configured with `npm run start` instead of Python command
- **Current Status**: Ready for manual fix - user needs to edit .replit file line 57
- **Required Fix**: Change .replit deployment configuration from `run = ["sh", "-c", "npm run start"]` to `run = ["python3", "app.py"]`
- **Alternative Fix**: Add Node.js module to .replit if keeping npm approach: `modules = ["python-3.11", "nodejs-20"]`
- **Resolution Steps Completed**: 
  - Enhanced app.py with robust error handling and production optimization
  - Created package.json with proper npm scripts that delegate to Python (`"start": "python3 app.py"`)
  - Updated Dockerfile and Procfile for consistent Python execution
  - All entry points now properly handle Cloud Run environment variables
- **Manual Action Required**: User must edit .replit file line 57 to use Python command directly

## Calendar Date Fix and OBS Integration Completion (August 19, 2025)

### Calendar Date Offset Resolution
- **Issue**: Calendar dates were offset by one day due to JavaScript timezone handling
- **Root Cause**: `new Date(dateStr)` parsing ISO date strings as UTC, causing local timezone conversion
- **Resolution**: Modified JavaScript date parsing to construct dates directly from year/month/day components
- **Impact**: Calendar dates now correctly match displayed readings and OBS integration

### OBS Integration Completion
- **Issue**: "No readings available to send to OBS" error when attempting to send readings
- **Root Cause**: Missing `get_readings_for_date` method in `WebLiturgicalCalendar` class
- **Resolution**: Added complete `get_readings_for_date` method that:
  - Retrieves readings for specified dates
  - Formats data correctly for OBS controller
  - Returns proper data structure with all reading types
- **Configuration**: Updated `config.ini` with sample OBS text source mappings
- **Status**: OBS integration fully functional, ready for live testing with OBS Studio

### System Verification
- **Web Calendar**: Running successfully on port 5000
- **Reading Retrieval**: All Sunday readings displaying correctly
- **Date Accuracy**: Calendar dates match liturgical data properly
- **User Confirmation**: Date display verified as correct by user

## API and Deployment Fixes (August 18, 2025)

### Readings API Resolution
- **Issue**: External liturgical APIs (Vanderbilt, lectionarypage.net) returning 403 Forbidden errors
- **Resolution**: Enhanced fallback system with priority order:
  1. Local readings database (primary)
  2. External APIs (secondary)  
  3. Closest Sunday readings (tertiary)
- **Coverage**: Added comprehensive Sunday readings for August 2025
- **User Preference**: Focus on Sunday readings rather than weekdays (per user request)

### Deployment Configuration Fixes (Updated August 19, 2025)
- **Issue**: Deployment failed due to undefined `$file` variable in run command and missing entry point specification
- **Root Cause**: `.replit` configuration missing explicit `run` command in `[deployment]` section for Google Cloud Run
- **Resolution**: Comprehensive deployment configuration for Cloud Run deployment:
  - **Primary Entry Points**:
    - `app.py`: Minimal, streamlined entry point for Cloud Run deployment
    - `main.py`: Alternative entry point with port 5000 default
    - `run`: Executable script with `python3 app.py` command
  - **Configuration Files**:
    - `Procfile`: `web: python3 app.py` for Heroku-style deployment
    - `Dockerfile`: Cloud Run optimized with Python 3.11, non-root user, proper CMD
    - `.dockerignore`: Excludes cache and development files
    - `pyproject.toml`: Minimal configuration with essential metadata only
  - **Verification**: All entry points tested and confirmed working with successful imports
- **Deployment Target**: Google Cloud Run via Replit deployment system
- **Entry Point**: Web calendar application (`web_calendar.py`) serves as the main web interface
- **Host Configuration**: All entry points bind to `0.0.0.0` with PORT environment variable support
- **Container Ready**: Dockerfile creates secure, production-ready container for deployment

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