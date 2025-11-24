# Trinity Church Streaming Design - macOS Installation Guide

## Quick Installation

### Option 1: Download Pre-Built App (Recommended)
If you have a pre-built `.app` file:

1. Download `Trinity Church Streaming.app`
2. Drag it to your **Applications** folder
3. Double-click to launch
4. The app will open in your default browser at `http://localhost:5000`

**First Launch Security:**
- macOS may show a security warning since this is not from the App Store
- Go to **System Preferences > Security & Privacy > General**
- Click "Open Anyway" next to the blocked app message

---

## Option 2: Build the App Yourself

### Prerequisites
- **macOS 10.13 or later**
- **Python 3.11 or higher** - Download from [python.org](https://www.python.org/downloads/)
- **Xcode Command Line Tools** (optional but recommended)

### Build Steps

1. **Download the project files** (ZIP from Replit or Git clone)

2. **Open Terminal** and navigate to the project folder:
   ```bash
   cd ~/Downloads/liturgical-calendar-web
   ```

3. **Make the build script executable:**
   ```bash
   chmod +x build_macos_app.sh
   ```

4. **Run the build script:**
   ```bash
   ./build_macos_app.sh
   ```

5. **Install the app:**
   - Open the `dist` folder
   - Drag `launcher.app` to your Applications folder
   - Rename it to `Trinity Church Streaming.app`

6. **Launch the app:**
   - Double-click the app in Applications
   - Your browser will open automatically

---

## Configuration

### OBS Studio Integration
If you use OBS Studio for streaming:

1. Enable OBS WebSocket:
   - Open OBS Studio
   - Go to **Tools > WebSocket Server Settings**
   - Enable the WebSocket server
   - Note the port (default: 4455)

2. Configure in the app:
   - Launch Trinity Church Streaming
   - Click the settings/OBS icon
   - Enter your OBS connection details

### ATEM Switcher Integration
If you have a Blackmagic ATEM video switcher:

1. Locate the app's `config.ini` file:
   ```bash
   ~/Applications/Trinity Church Streaming.app/Contents/Resources/config.ini
   ```

2. Edit the ATEM section:
   ```ini
   [ATEM]
   ip_address = 192.168.1.240
   port = 20890
   ```

3. Restart the app for changes to take effect

---

## Features

✅ **Liturgical Calendar** - Browse Episcopal liturgical readings  
✅ **Title Cards** - Generate broadcast-quality title cards with liturgical colors  
✅ **Lower Thirds** - Create lower third graphics for scripture readings  
✅ **Concert Programs** - Generate concert program graphics  
✅ **Announcement Slides** - Create announcement slides (4 types)  
✅ **Service Order Slides** - Display order of service  
✅ **Countdown Timers** - Pre-service countdown graphics  
✅ **Dark Mode** - Toggle dark mode for comfortable viewing  
✅ **OBS Integration** - Send readings directly to OBS Studio  
✅ **ATEM Control** - Control Blackmagic ATEM video switchers  

---

## Troubleshooting

### App Won't Open - Security Warning
**Solution:**
1. Go to **System Preferences > Security & Privacy**
2. Click the **General** tab
3. Click **Open Anyway** next to the app name
4. Try launching again

### "Python Not Found" Error
**Solution:**
1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Rebuild the app using the build script

### Port 5000 Already in Use
**Solution:**
1. Check if another app is using port 5000:
   ```bash
   lsof -i :5000
   ```
2. Stop the conflicting app or edit `launcher.py` to use a different port

### Browser Doesn't Open Automatically
**Solution:**
- Manually open your browser to: `http://localhost:5000`

### OBS Connection Failed
**Solution:**
1. Verify OBS Studio is running
2. Check WebSocket server is enabled in OBS
3. Verify port number matches (default: 4455)
4. Check firewall settings aren't blocking connections

---

## Uninstallation

1. Drag `Trinity Church Streaming.app` from Applications to Trash
2. Remove configuration file (optional):
   ```bash
   rm -rf ~/Library/Application\ Support/TrinityChurchStreaming
   ```

---

## Support

This application is provided as public domain software.

**Credits:** Philippe Beaudette / Trinity Episcopal Church, Tulsa, OK

**Issues or Questions?** Check the documentation or contact your system administrator.

---

## Version

**Current Version:** 2.4.9

**Last Updated:** November 2025
