#!/bin/bash
# Build script for creating macOS application bundle
# Trinity Church Streaming Design

set -e  # Exit on error

echo "======================================"
echo "Trinity Church Streaming Design"
echo "macOS Application Builder"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.11 or higher from python.org"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install py2app if not installed
echo "Installing/updating py2app..."
pip3 install --upgrade py2app

# Install all dependencies
echo "Installing application dependencies..."
pip3 install -r requirements.txt || pip3 install beautifulsoup4 flask gunicorn obsws-python opencv-python pdfplumber pillow pyatemmax pypdf2 pytesseract requests trafilatura werkzeug

echo ""
echo "Building macOS application bundle..."
echo ""

# Clean previous builds
rm -rf build dist

# Build the app
python3 setup_macos.py py2app

echo ""
echo "======================================"
echo "Build Complete!"
echo "======================================"
echo ""
echo "Your application is located at:"
echo "  dist/launcher.app"
echo ""
echo "To install:"
echo "  1. Open the 'dist' folder"
echo "  2. Drag 'launcher.app' to your Applications folder"
echo "  3. Rename it to 'Trinity Church Streaming.app'"
echo "  4. Double-click to launch"
echo ""
echo "Note: On first launch, macOS may ask you to allow"
echo "the app to run. Go to System Preferences > Security"
echo "& Privacy if you see a security warning."
echo ""
