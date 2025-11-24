"""
macOS Application Setup for Trinity Church Streaming Design
Uses py2app to create a standalone macOS application bundle
"""

from setuptools import setup

APP = ['launcher.py']
DATA_FILES = [
    ('', ['web_calendar.py', 'atem_controller.py', 'liturgy_fetcher.py', 'config.ini']),
    ('data', ['year_a_readings.json', 'year_b_readings.json', 'year_c_readings.json']),
    ('templates', ['templates/calendar.html']),
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'flask',
        'beautifulsoup4',
        'requests',
        'PIL',
        'pdfplumber',
        'PyPDF2',
        'pytesseract',
        'trafilatura',
        'werkzeug',
        'obsws_python',
        'PyATEMMax',
        'cv2',
    ],
    'includes': [
        'web_calendar',
        'atem_controller',
        'liturgy_fetcher',
        'configparser',
        'logging',
        'json',
        'datetime',
        'zipfile',
        'io',
        'os',
        're',
    ],
    'excludes': ['tkinter', 'matplotlib', 'numpy'],
    'iconfile': 'app_icon.icns',  # Optional: Add custom icon
    'plist': {
        'CFBundleName': 'Trinity Church Streaming',
        'CFBundleDisplayName': 'Trinity Church Streaming Design',
        'CFBundleIdentifier': 'org.trinitychurch.streamingdesign',
        'CFBundleVersion': '2.4.9',
        'CFBundleShortVersionString': '2.4.9',
        'NSHumanReadableCopyright': 'Public Domain - Philippe Beaudette/Trinity Episcopal Church, Tulsa, OK',
        'LSMinimumSystemVersion': '10.13',
        'LSUIElement': False,  # Show in Dock
    }
}

setup(
    name='TrinityChurchStreaming',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
