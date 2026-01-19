# Overview

This project is a Daily Liturgical Scripture OBS Automation system designed for the Episcopal Church. It automates the process of fetching liturgical readings from the Revised Common Lectionary, formatting them, and updating text sources within OBS Studio via WebSocket for live streaming or recording. The system also includes a web-based liturgical calendar for browsing readings and integrates with Blackmagic ATEM video switchers. Its primary purpose is to streamline the creation of broadcast-ready graphics and manage live production elements for church services.

# User Preferences

Preferred communication style: Simple, everyday language.

## Form Field Preferences
- **Music Credits**: Prelude composer and postlude composer fields have been removed from all service forms (Eucharist, Special Services, Evensong). Only prelude/postlude titles are collected.

## Deployment Preferences
- **Version Updates**: When updating version number and deploying, always update both:
  1. Version number in `pyproject.toml`
  2. Footer version number in `templates/calendar.html`
- **macOS Application Bundle**: Project includes py2app configuration for creating standalone macOS application. Run `./build_macos_app.sh` to build.

# System Architecture

## Core Components

The application features a modular architecture:
- **LiturgyFetcher**: Retrieves Episcopal liturgical calendar data and scripture readings from multiple sources using web scraping.
- **OBSController**: Manages WebSocket communication with OBS Studio for updating text sources.
- **ATEMController**: Manages network communication with Blackmagic ATEM video switchers via PyATEMMax library.
- **ScriptureParser**: Formats liturgical readings for display.
- **Main Application Controller**: Orchestrates the workflow, manages configuration, and handles logging.
- **Interactive Liturgical Calendar**: A Flask web interface providing a visual calendar with month navigation, liturgical color coding, reading previews, OBS integration, and ATEM switcher control.

## UI/UX Decisions

- **Liturgical Season Colors**: Dynamic adaptation of graphics to match liturgical season colors (Advent, Christmas, Epiphany, Lent, Easter, Pentecost).
- **Lower Thirds Layout**: Broadcast-style design with abstract, angled edges, layered elements, and dynamic liturgical color themes. Five selectable lower third design styles are available: Classic, Minimal, Modern Glass, Bold Banner, and Elegant.
- **Mobile Responsive Design**: Comprehensive mobile-responsive interface across all screen sizes.
- **Broadcast Graphics**: Full-screen title cards and lower thirds are dynamically generated with liturgical season-themed designs, decorative elements, and specific typography (Stack Sans font family). Graphics previews are available.
- **Dark Mode Support**: Full dark mode implementation with toggle button and localStorage persistence.
- **Modern Dashboard UI**: Redesigned main page with a cleaner look, compact header, and reorganized collapsible sidebar sections (Quick Actions, Service Options, Readings, Advanced Tools, Export, Quick Guide).
- **Service Preparation Wizard**: A guided, step-by-step workflow for preparing complete service graphics packages, accessible at `/wizard`.

## Technical Implementations

- **PDF Upload**: Drag-and-drop PDF upload with text extraction and smart liturgical content detection.
- **Service Details Interview**: Modal form for gathering service information (hymns, musicians, clergy, scripture references) with local storage and server backup.
- **Text Export**: ZIP export for liturgical readings and service details, creating individual text files.
- **Dynamic Service Details Form**: Unified interface that adapts based on selected service type (Eucharist, Evensong, Special Services, Funeral) with independent data storage. Evensong includes automatic fetching of Evening Prayer readings.
- **OBS Scene Collection Export**: Generation of OBS scene collection JSON for seamless import.
- **Custom Graphics Generators**: On-demand custom title card, lower third, announcement slide, service order slide, and countdown timer generators with customizable text, liturgical season themes, and memorial service options.
- **ATEM Video Switcher Integration**: Comprehensive Blackmagic ATEM video switcher control, including connection management, program/preview switching, transitions, and audio control.
- **Liturgical Season Override**: Option to override automatic season detection in the service details form for all generated graphics.

## Configuration Management

- INI-based configuration for OBS connection settings, scene mappings, ATEM switcher connection settings, ATEM input mappings, and API preferences.

## Error Handling Strategy

- Graceful degradation with multiple API fallbacks.
- Connection resilience for OBS and ATEM with logging of failures.

## Data Flow Architecture

1.  **Fetch Phase**: Retrieve liturgical data.
2.  **Parse Phase**: Structure and format readings.
3.  **Connect Phase**: Establish WebSocket connection to OBS.
4.  **Update Phase**: Push formatted text to OBS sources.

# External Dependencies

## Required Libraries
- **obsws-python**: OBS Studio WebSocket client.
- **PyATEMMax**: Blackmagic ATEM video switcher control library.
- **requests**: HTTP client.
- **configparser**: Configuration file management.
- **logging**: Application logging.
- **BeautifulSoup**: Web scraping.
- **pdfplumber**: PDF text extraction.

## External APIs
- **The Lectionary Page (lectionarypage.net)**: Primary source for Episcopal RCL readings.
- **Vanderbilt Divinity Library RCL**: Fallback source for Revised Common Lectionary.
- **Hymnary.org**: Used for fetching hymn texts.

## System Requirements
- **OBS Studio**: Must be running with WebSocket server enabled.
- **Python 3.x**: Runtime environment.
- **Network Access**: For external API calls.