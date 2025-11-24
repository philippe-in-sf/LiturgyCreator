# Building Trinity Church Streaming Design for macOS

This guide explains how to build a standalone macOS application from this project.

## Quick Start

Run the build script:

```bash
./build_macos_app.sh
```

The script will:
1. Check for Python 3.11+
2. Install py2app and dependencies
3. Build the application bundle
4. Create `dist/launcher.app`

## What Gets Built

The build process creates a complete macOS application bundle that includes:

- ✅ Python runtime
- ✅ All Python dependencies (Flask, PIL, etc.)
- ✅ All project code and templates
- ✅ Liturgical calendar data (Years A, B, C)
- ✅ Configuration files
- ✅ Auto-launching web interface

## Installation

After building:

1. Open the `dist` folder
2. Drag `launcher.app` to Applications
3. Rename to `Trinity Church Streaming.app`
4. Double-click to launch

## Manual Build Steps

If you prefer to build manually:

```bash
# Install py2app
pip3 install py2app

# Install dependencies
pip3 install -r requirements.txt

# Build the app
python3 setup_macos.py py2app

# Result will be in dist/launcher.app
```

## Build Requirements

- macOS 10.13 or later
- Python 3.11 or higher
- pip3
- ~500MB disk space for build process

## Customization

### Change App Name
Edit `setup_macos.py`:
```python
'CFBundleDisplayName': 'Your Custom Name Here',
```

### Add Custom Icon
1. Create or obtain an `.icns` file
2. Name it `app_icon.icns`
3. Place it in the project root
4. The build script will automatically include it

### Change Port
Edit `launcher.py`:
```python
PORT = 5000  # Change to your desired port
```

## Troubleshooting

### "Module not found" during build
**Solution:** Install the missing module:
```bash
pip3 install <module-name>
```

### Build fails with "permission denied"
**Solution:** Make the script executable:
```bash
chmod +x build_macos_app.sh
```

### Large app size
**Solution:** The app bundle includes Python and all dependencies (~200-300MB). This is normal for standalone Python apps.

### App won't open after build
**Solution:** Check the Console app for error messages. Common issues:
- Missing dependencies
- Incorrect file paths in setup_macos.py
- Python version mismatch

## Distribution

To share the app with others:

1. **ZIP the app:**
   ```bash
   cd dist
   zip -r "Trinity Church Streaming.zip" "launcher.app"
   ```

2. **Upload to file sharing:**
   - Google Drive
   - Dropbox
   - Your church website

3. **Include installation instructions:**
   - Provide `MACOS_INSTALLATION.md` to users

### Code Signing (Optional)

For wider distribution without security warnings:

1. Get an Apple Developer account ($99/year)
2. Sign the app:
   ```bash
   codesign --deep --force --sign "Developer ID Application: Your Name" dist/launcher.app
   ```
3. Notarize with Apple (required for macOS 10.15+)

## Version Updates

When updating the app version:

1. Update `pyproject.toml` version number
2. Update `templates/calendar.html` footer version
3. Update `setup_macos.py` CFBundleVersion
4. Rebuild the app

## File Structure

```
dist/launcher.app/
├── Contents/
│   ├── Info.plist          # App metadata
│   ├── MacOS/
│   │   └── launcher        # Executable
│   └── Resources/
│       ├── web_calendar.py
│       ├── atem_controller.py
│       ├── config.ini
│       ├── templates/
│       ├── data/
│       └── lib/            # Python packages
```

## Advanced: Creating DMG Installer

For professional distribution:

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Trinity Church Streaming" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "Trinity-Church-Streaming.dmg" \
  "dist/"
```

Users can then drag the app to Applications from the DMG.

---

**Version:** 2.4.9  
**Last Updated:** November 2025
