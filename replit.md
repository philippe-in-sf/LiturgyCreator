# Overview

This project is a Daily Liturgical Scripture OBS Automation system that fetches Episcopal Church liturgical readings from The Lectionary Page (Revised Common Lectionary) and automatically updates text sources in OBS Studio via WebSocket connections. The system retrieves daily scripture readings based on the Episcopal liturgical calendar, parses them into a formatted structure, and displays them in configured OBS scenes for live streaming or recording purposes.

# User Preferences

Preferred communication style: Simple, everyday language.

## Deployment Preferences
- **Version Updates**: When updating version number and deploying, always update both:
  1. Version number in `pyproject.toml` 
  2. Footer version number in `templates/calendar.html`

# System Architecture

## Core Components

The application follows a modular architecture with five main components:

- **LiturgyFetcher Module**: Handles fetching Episcopal liturgical calendar data and scripture readings from RCL sources, using a fallback system with multiple sources (The Lectionary Page and Vanderbilt Divinity Library) and web scraping.
- **OBSController Module**: Manages WebSocket connection and communication with OBS Studio using the `obsws-python` library, supporting configurable host, port, password, and scene mappings.
- **ScriptureParser Module**: Parses and formats liturgical readings for display, including scripture reference abbreviations and text formatting.
- **Main Application Controller**: Orchestrates the entire automation workflow with INI-file based configuration management and dual logging.
- **Interactive Liturgical Calendar**: Provides a visual calendar interface (Flask web interface) for browsing liturgical seasons and readings, featuring month navigation, liturgical color coding, reading preview, and OBS integration. It tracks the Episcopal liturgical year and detects seasons/feast days.

## UI/UX Decisions

- **Liturgical Season Colors**: Lower third graphics dynamically adapt to liturgical season colors (Advent, Christmas, Epiphany, Lent, Easter, Pentecost) for appropriate visual themes.
- **Lower Thirds Layout**: Positioned at 5/6 of screen height with a 260-pixel text indent, reserving space for a church logo.
- **Mobile Responsive Design**: Comprehensive mobile-responsive interface for all screen sizes, including tablet (single-column, stacked buttons) and mobile (compact layout, optimized touch targets, responsive modals, adjustable font sizes).
- **OBS Path Configuration**: Settings interface for OBS file path configuration with OS selection, base path configuration, and localStorage persistence for scene generation.

## Technical Implementations

- **PDF Upload (BETA)**: Drag-and-drop PDF upload with text extraction using `pdfplumber` (with OCR fallback), smart liturgical content detection, and integration into the calendar interface.
- **Service Details Interview**: A modal form for gathering service information (hymns, musicians, clergy) with local browser storage and server backup, extending OBS integration to include these details.
- **Text Export Functionality**: ZIP export for liturgical readings and service details via a new API endpoint, creating individual text files (scripture text, references, service details) formatted with 50-character line width and word wrapping.
- **Calendar Date Offset Resolution**: JavaScript date parsing modified to correctly handle timezones and prevent one-day offsets.
- **Deployment Configuration**: Comprehensive configuration for Google Cloud Run deployment, including `Procfile`, `Dockerfile`, `.dockerignore`, and `pyproject.toml` settings, ensuring Python 3.11 execution and proper port binding.
- **Readings API Resolution**: Enhanced fallback system for liturgical APIs (local database, external APIs, closest Sunday readings) to ensure readings are always available.
- **OBS Scene Collection Export (v2.2.0)**: Complete rewrite of OBS scene collection JSON generation to match native OBS Studio format specification, including proper source definitions, scene structure, transitions array, scene order, and all required metadata fields for successful import into OBS Studio.

## Configuration Management

- INI-based configuration files for OBS connection settings, scene mappings, and API preferences.

## Error Handling Strategy

- Graceful degradation with multiple API fallbacks.
- Connection resilience for OBS, logging failures without crashing.
- Comprehensive logging for debugging and monitoring.

## Data Flow Architecture

1.  **Fetch Phase**: Retrieve liturgical data from external APIs.
2.  **Parse Phase**: Structure and format scripture readings.
3.  **Connect Phase**: Establish WebSocket connection to OBS.
4.  **Update Phase**: Push formatted text to configured OBS sources.

# External Dependencies

## Required Libraries
- **obsws-python**: WebSocket client for OBS Studio communication.
- **requests**: HTTP client for API calls to liturgical services.
- **configparser**: Configuration file management.
- **logging**: Application logging and monitoring.
- **BeautifulSoup**: Used for web scraping HTML content.
- **pdfplumber**: For PDF text extraction.

## External APIs
- **The Lectionary Page (lectionarypage.net)**: Primary source for Episcopal RCL readings and calendar data.
- **Vanderbilt Divinity Library RCL**: Fallback source for Revised Common Lectionary scripture readings.

## System Requirements
- **OBS Studio**: Must be running with WebSocket server enabled.
- **Python 3.x**: Runtime environment for the automation script.
- **Network Access**: Required for fetching liturgical data from external APIs.