# Overview

This project is a Daily Liturgical Scripture OBS Automation system designed for the Episcopal Church. It fetches liturgical readings from the Revised Common Lectionary, processes them, and automatically updates text sources within OBS Studio via WebSocket for live streaming or recording. The system includes a web-based liturgical calendar for browsing and managing readings.

# User Preferences

Preferred communication style: Simple, everyday language.

## Form Field Preferences
- **Music Credits**: Prelude composer and postlude composer fields have been removed from all service forms (Eucharist, Special Services, Evensong). Only prelude/postlude titles are collected.

## Deployment Preferences
- **Version Updates**: When updating version number and deploying, always update both:
  1. Version number in `pyproject.toml` 
  2. Footer version number in `templates/calendar.html`

# System Architecture

## Core Components

The application features a modular architecture:
- **LiturgyFetcher**: Retrieves Episcopal liturgical calendar data and scripture readings from multiple sources (The Lectionary Page, Vanderbilt Divinity Library) using web scraping.
- **OBSController**: Manages WebSocket communication with OBS Studio for updating text sources.
- **ScriptureParser**: Formats liturgical readings for display.
- **Main Application Controller**: Orchestrates the workflow, manages configuration, and handles logging.
- **Interactive Liturgical Calendar**: A Flask web interface providing a visual calendar with month navigation, liturgical color coding, reading previews, and OBS integration. It tracks the Episcopal liturgical year and detects seasons/feast days.

## UI/UX Decisions

- **Liturgical Season Colors**: Dynamic adaptation of lower third graphics to match liturgical season colors (Advent, Christmas, Epiphany, Lent, Easter, Pentecost).
- **Lower Thirds Layout**: Broadcast-style design with abstract, angled edges, layered elements, and dynamic liturgical color themes, positioned at 5/6 screen height with text starting at 1/5 from the left.
- **Mobile Responsive Design**: Comprehensive mobile-responsive interface across all screen sizes.
- **OBS Path Configuration**: Settings interface for OBS file path configuration with OS selection and base path configuration.
- **Broadcast Graphics**: Full-screen title cards and lower thirds are dynamically generated with liturgical season-themed designs, decorative elements, and specific typography.
- **Graphics Previews**: Preview functionality for title cards and lower thirds before download.

## Technical Implementations

- **PDF Upload**: Drag-and-drop PDF upload with text extraction and smart liturgical content detection.
- **Service Details Interview**: Modal form for gathering service information (hymns, musicians, clergy, scripture references) with local storage and server backup.
- **Text Export**: ZIP export for liturgical readings and service details, creating individual text files with formatted content.
- **Dynamic Service Details Form**: Unified interface that adapts based on selected service type (Eucharist, Evensong, Funeral), displaying relevant fields and independently storing data for each.
- **Service Type Support**: Multi-service type architecture (Eucharist, Evensong, Special Services, Funeral) with independent readings and service details. Evensong includes automatic fetching of Evening Prayer readings from the Daily Office Lectionary. Funeral services utilize a black and white visual theme for graphics.
- **OBS Scene Collection Export**: Generation of OBS scene collection JSON conforming to native OBS Studio format for seamless import.
- **Calendar Date Offset Resolution**: JavaScript date parsing for correct timezone handling.
- **Deployment Configuration**: Google Cloud Run deployment configuration (Procfile, Dockerfile, pyproject.toml).
- **Readings API Resolution**: Enhanced fallback system for liturgical APIs.
- **Folder Naming Standardization**: Consistent ZIP export folder structure ("lower_thirds", "readings", "service_details").
- **Blank Lower Third Template**: All ZIP exports include a blank lower third template (BLANK_TEMPLATE.png) with liturgical or funeral season colors for manual service element additions.
- **Custom Title Card Generator**: On-demand custom title card generation feature allowing users to create title cards with custom text, optional liturgical season colors, and funeral theme support. Perfect for video editing purposes and creating title cards for past services.
- **Organized Action Buttons (v2.3.9)**: Action buttons reorganized into three clear sections (Basic, Advanced, Export) for better usability and reduced visual clutter.
- **Custom Title Card Liturgical Season Selector (v2.4.0)**: Replaced date picker with dropdown menu for selecting liturgical seasons directly in custom title card generator, making it easier to choose colors without knowing specific dates.
- **Corrected Advent Liturgical Colors (v2.4.1)**: Updated Advent liturgical color from purple to royal blue per Episcopal tradition.
- **Removed Composer Fields (v2.4.3)**: Removed prelude composer and postlude composer fields from all service forms (Eucharist, Special Services, Evensong) per user preference. Only prelude/postlude titles are now collected.
- **Concert Program Feature (v2.4.3)**: Added comprehensive concert program creation with grey-themed graphics. Includes title card generation with performer name, date, and time, plus dynamic form for up to 10 concert pieces. Generates lower thirds for each piece with neutral grey theme suitable for concert broadcasts. Uses new theme system that supports both liturgical (seasonal colors) and concert (grey/neutral) styling.
- **Concert Graphics Enhancements (v2.4.4)**: Improved concert program readability and usability. Added black text outline (4px for titles, 3px for secondary text) to concert lower thirds for better visibility on grey backgrounds. Implemented preview functionality allowing users to see title card and all piece lower thirds before downloading. Fixed filtering logic to accept pieces with either title or composer (previously required both), with smart text formatting for partial entries.
- **Custom Lower Third Generator (v2.4.5)**: Added one-off custom lower third generation feature similar to custom title card generator. Users can create custom lower thirds with their own label/type and content text, select liturgical season colors from dropdown menu, and use memorial service theme (black/white) for memorial services. Perfect for special announcements, custom elements, or editing videos from previous weeks.

## Configuration Management

- INI-based configuration for OBS connection settings, scene mappings, and API preferences.

## Error Handling Strategy

- Graceful degradation with multiple API fallbacks.
- Connection resilience for OBS with logging of failures.
- Comprehensive logging for debugging.

## Data Flow Architecture

1.  **Fetch Phase**: Retrieve liturgical data.
2.  **Parse Phase**: Structure and format readings.
3.  **Connect Phase**: Establish WebSocket connection to OBS.
4.  **Update Phase**: Push formatted text to OBS sources.

# External Dependencies

## Required Libraries
- **obsws-python**: OBS Studio WebSocket client.
- **requests**: HTTP client.
- **configparser**: Configuration file management.
- **logging**: Application logging.
- **BeautifulSoup**: Web scraping.
- **pdfplumber**: PDF text extraction.

## External APIs
- **The Lectionary Page (lectionarypage.net)**: Primary source for Episcopal RCL readings.
- **Vanderbilt Divinity Library RCL**: Fallback source for Revised Common Lectionary.
- **Hymnary.org**: Used for fetching hymn texts (Evensong feature).

## System Requirements
- **OBS Studio**: Must be running with WebSocket server enabled.
- **Python 3.x**: Runtime environment.
- **Network Access**: For external API calls.