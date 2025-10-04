# Deployment Guide

## Overview
The Liturgical Calendar Web Application is now properly configured for deployment with multiple entry points to ensure compatibility with various deployment platforms.

## Entry Points Available

### 1. Primary Entry Point: `app.py`
- **Purpose**: Main Flask application entry point
- **Usage**: `python app.py`
- **Features**: 
  - Environment variable support for PORT
  - Production-ready configuration
  - Binds to 0.0.0.0 for external access

### 2. Alternative Entry Point: `main.py`
- **Purpose**: Enhanced entry point with detailed logging
- **Usage**: `python main.py`
- **Features**:
  - Debug mode control via environment variables
  - Startup status messages
  - Flexible configuration

### 3. Universal Entry Point: `run.py`
- **Purpose**: Universal deployment script
- **Usage**: `python run.py`
- **Features**:
  - Deployment-optimized configuration
  - Environment detection
  - User-friendly startup messages

### 4. Process Configuration: `Procfile`
- **Purpose**: Heroku-style process definition
- **Content**: `web: python app.py`
- **Usage**: For platforms that use Procfile for process management

## Deployment Configuration

### Environment Variables
- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False for production)
- `ENVIRONMENT`: Set to 'development' for debug mode

### Host Configuration
- All entry points bind to `0.0.0.0:5000` by default
- Supports external connections for deployment platforms
- Port 5000 is pre-configured for Replit deployment compatibility

### Dependencies
Dependencies are managed through `pyproject.toml`:
- beautifulsoup4>=4.13.4
- flask>=3.1.1
- obsws-python>=1.8.0
- requests>=2.32.4
- trafilatura>=2.0.0

## Deployment Commands

### For Replit Deployment
The application will automatically use the Web Calendar workflow which runs:
```
python web_calendar.py
```

### For Other Platforms
Choose any of these commands:
```bash
python app.py
python main.py
python run.py
python server.py
```

### 5. Production Server Entry Point: `server.py`
- **Purpose**: Optimized entry point for Replit deployment
- **Usage**: `python server.py`
- **Features**:
  - Production-optimized configuration
  - Clear startup logging
  - Deployment platform compatibility
  - Automatic port detection from environment

### 6. Docker Configuration: `Dockerfile`
- **Purpose**: Containerized deployment option
- **Usage**: `docker build -t liturgical-calendar . && docker run -p 5000:5000 liturgical-calendar`
- **Features**:
  - Python 3.11 slim base image
  - Automatic dependency installation
  - Production environment configuration

## Application Features
- Interactive liturgical calendar with Episcopal Church calendar integration
- Daily scripture readings from The Lectionary Page
- Month-by-month navigation with liturgical colors
- Responsive web interface
- API endpoints for calendar data and readings

## Version Management

### Incrementing Version Numbers
When releasing a new version, you must update the version number in **TWO** locations:

1. **Backend Version** (`web_calendar.py`):
   - Located in the docstring at the top of the file
   - Format: `Version: X.Y - Description`
   - Example: `Version: 1.8 - Password Protected`

2. **Frontend Display** (`templates/calendar.html`):
   - Located in the footer section at the bottom of the file
   - Format: `<strong>Episcopal Liturgical Calendar Tool vX.Y</strong>`
   - Example: `<strong>Episcopal Liturgical Calendar Tool v1.8</strong>`

### Version Update Checklist
Before releasing a new version:
- [ ] Update version number in `web_calendar.py` docstring
- [ ] Update version number in `templates/calendar.html` footer
- [ ] Verify both version numbers match
- [ ] Document changes in version description
- [ ] Test application functionality
- [ ] Restart workflow to apply changes

### Version Numbering Scheme
- **Major version** (X.0): Significant feature additions or breaking changes
- **Minor version** (X.Y): New features, improvements, or bug fixes
- Use descriptive tags: "Password Protected", "Complete Export", etc.

## Verification
The deployment has been tested and verified to:
✅ Serve the web application correctly on port 5000
✅ Handle HTTP requests and return proper HTML responses
✅ Support external connections via 0.0.0.0 binding
✅ Load all required dependencies successfully