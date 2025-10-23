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
- **Lower Thirds Layout**: Positioned at 5/6 of screen height with text content starting at approximately 1/5 from the left edge (384px on 1920px width), creating clean blank space on the left side.
- **Broadcast-Style Lower Thirds**: Abstract, artistic broadcast design with dramatic angled edges and 9 layered elements: gradient background (dark to light), multiple angled panels with varied shades, bright accent stripes, diagonal elements for visual interest, and full-width top/bottom accent stripes. The design is dominated by shades of the liturgical season color (e.g., very dark green to very light green for Pentecost season) creating depth and visual complexity while maintaining the reverent color theme.
- **Mobile Responsive Design**: Comprehensive mobile-responsive interface for all screen sizes, including tablet (single-column, stacked buttons) and mobile (compact layout, optimized touch targets, responsive modals, adjustable font sizes).
- **OBS Path Configuration**: Settings interface for OBS file path configuration with OS selection, base path configuration, and localStorage persistence for scene generation.

## Technical Implementations

- **PDF Upload (BETA)**: Drag-and-drop PDF upload with text extraction using `pdfplumber` (with OCR fallback), smart liturgical content detection, and integration into the calendar interface.
- **Service Details Interview**: A modal form for gathering service information (hymns, musicians, clergy, and scripture reading references) with local browser storage and server backup, extending OBS integration to include these details. The form is organized in liturgical order and pre-populates scripture reading references from the day's lectionary, which users can override with custom references if needed. When overrides are provided, both the preview and export functions will use the custom references instead of the default lectionary readings.
- **Text Export Functionality**: ZIP export for liturgical readings and service details via a new API endpoint, creating individual text files (scripture text, references, service details) formatted with 50-character line width and word wrapping.
- **Calendar Date Offset Resolution**: JavaScript date parsing modified to correctly handle timezones and prevent one-day offsets.
- **Deployment Configuration**: Comprehensive configuration for Google Cloud Run deployment, including `Procfile`, `Dockerfile`, `.dockerignore`, and `pyproject.toml` settings, ensuring Python 3.11 execution and proper port binding.
- **Readings API Resolution**: Enhanced fallback system for liturgical APIs (local database, external APIs, closest Sunday readings) to ensure readings are always available.
- **OBS Scene Collection Export (v2.2.0)**: Complete rewrite of OBS scene collection JSON generation to match native OBS Studio format specification, including proper source definitions, scene structure, transitions array, scene order, and all required metadata fields for successful import into OBS Studio.
- **Full-Screen Title Card (v2.2.1)**: Automatic generation of a 1920x1080 title card image with 50% white opacity, displaying the liturgical reference (e.g., "First Sunday of Advent") centered at the top and "Trinity Episcopal Church, Tulsa, OK" at the bottom, styled with liturgical season colors matching the lower thirds.
- **Enhanced Title Card Design (v2.2.2)**: Eye-catching title card design with decorative borders, corner flourishes, horizontal dividers with diamond ornaments, text shadows with black outlines for depth, and elegant serif typography (65pt for liturgical reference, 70pt for church name and calendar date)—all using dynamic liturgical season accent colors for visual impact while maintaining reverent aesthetics. Layout displays the liturgical reference (e.g., "The 19th Sunday after Pentecost") above the first separator, the calendar date just below the first separator, the church logo centered in the middle, and "Trinity Episcopal Church, Tulsa, OK" below the second separator. The liturgical reference automatically strips "Proper X" prefixes (e.g., "Proper 24 (Sunday after Pentecost)" → "Sunday after Pentecost").
- **Church Logo Integration (v2.2.3)**: Integrated Trinity Episcopal Church logo into Title Card graphics, positioned in the center of the card with automatic scaling to fit within the reserved space, maintaining aspect ratio.
- **Graphics Preview Modal (v2.2.4)**: Added preview functionality allowing users to view title card and lower thirds graphics before downloading, with a modal display showing base64-encoded images and direct download option from the preview.
- **Special Services Feature (v2.2.5)**: Comprehensive non-lectionary service support with a dedicated modal form for manual reading entry (Gospel, Old Testament, Epistle, Psalm with reference and text fields), service details collection (hymns, musicians, clergy), and automatic generation of custom title cards and lower thirds graphics for weddings, funerals, memorial services, and other special occasions that occur outside the regular lectionary calendar.
- **Evensong Service Type Support (v2.3.0)**: Multi-service type architecture allowing users to toggle between Eucharist and Evensong services for the same date, with independent readings and service details for each service type. Features include: prominent service type selector in the calendar interface (defaults to Eucharist for backward compatibility), nested data storage structure organizing readings and service details by date and service type, API endpoints that accept service_type parameter with proper defaults, automatic differentiation in exports (folder names and title cards include service type), and automatic fetching of Evening Prayer readings from the Daily Office Lectionary (BCP Online). The system uses computus algorithms to calculate Easter and other movable feasts, enabling accurate liturgical season detection (Advent, Christmas, Epiphany, Lent, Easter, Pentecost) for proper Daily Office Lectionary page routing. Evening Prayer readings include psalms (extracted from the portion after "v" separator) and scripture references (Old Testament, Epistle, Gospel) appropriate to the Daily Office 2-year cycle. The system maintains complete separation of data between service types while preserving the existing workflow simplicity.
- **Evensong Service Construction (v2.3.1)**: Dedicated modal form for building complete Evensong services with specialized fields for Evening Prayer liturgy. The "Construct Evensong" button appears in the interface when Evensong service type is selected, providing structured input for Responsory Composer, Evening Hymn, First Reading Reference, Magnificat Setting and Composer, Second Reading Reference, and Nunc Dimittis Setting and Composer. Additional optional fields include organist, prelude, and postlude information. The form generates a comprehensive ZIP export containing text files for all service details formatted with 50-character line width, a title card displaying "Evensong" with the service date, and lower third graphics for Evening Hymn, Magnificat, Nunc Dimittis, and scripture readings. Hymn text is automatically fetched from Hymnary.org when available. All graphics maintain liturgical season color theming for visual consistency.
- **Evensong Form Liturgical Order Correction (v2.3.2)**: Corrected the Evensong Service Construction form to follow proper Evening Prayer liturgical order with four distinct sections: (1) Invitatory and Psalter (Responsory Composer, Preces and Responses Setting/Composer, Office Hymn, First/Second Psalm Reference and Composer), (2) The Lessons (First Lesson, Magnificat Setting/Composer, Second Lesson, Nunc Dimittis Setting/Composer), (3) Prayers (Responses Setting/Composer, Anthem), and (4) Conclusion (Hymn, Postlude). The form now includes 19 comprehensive fields organized in liturgical sequence, with text file exports for all fields, hymn text fetching for both Office Hymn and closing Hymn, and lower third graphics generation for Office Hymn, First Lesson, Magnificat, Second Lesson, Nunc Dimittis, Anthem, and Hymn.
- **Dynamic Service Details Form (v2.3.3)**: Unified Service Details interface that dynamically adapts based on selected service type. When Eucharist is selected, the form displays traditional Eucharist fields (Prelude, Opening Hymn, Scripture Readings with RCL auto-population, Sequence Hymn, Sermon & Offertory, Communion, Closing). When Evensong is selected, the form automatically switches to Evening Prayer fields organized in proper liturgical order (Invitatory and Psalter, The Lessons with Daily Office auto-population, Prayers, Conclusion). The implementation uses separate field containers with unique ID namespaces to prevent conflicts, maintains independent data storage for each service type, and eliminates the need for separate modals. Users experience seamless switching between service types while preserving their saved data for each service independently.

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