"""Regression coverage for the wizard's downloadable graphics package."""

import io
import unittest
import zipfile
from unittest.mock import patch

from web_calendar import app


class WizardExportTest(unittest.TestCase):
    @patch('web_calendar.WebLiturgicalCalendar')
    @patch('web_calendar.load_branding_config')
    def test_download_contains_graphics_and_matching_summary(self, branding, calendar):
        branding.return_value = {
            'church_name': 'Test Church',
            'logo_path': None,
            'custom_colors': {'enabled': False},
            'custom_font': {'enabled': False},
        }
        calendar.return_value.get_liturgical_info.return_value = {
            'feast_day': 'St. Michael and All Angels',
            'is_sunday': False,
        }
        payload = {
            'date': '2026-09-29',
            'serviceType': 'eucharist',
            'style': 'classic',
            'serviceDetails': {'openingHymn': 'Praise, my soul'},
            'readings': {'first_reading': {
                'reference': 'Genesis 28:10-17',
                'text': 'Jacob dreamed of a ladder.',
            }},
            'extras': {
                'includeAnnouncements': True,
                'announcements': [{'title': 'Parish picnic', 'type': 'general', 'fields': {}}],
                'includeServiceOrder': True,
                'serviceOrderItems': ['Opening hymn'],
                'includeCountdown': True,
                'countdownTimes': [5],
                'includeCustomTitleSlide': True,
                'customTitleText': 'Welcome',
                'includeCustomLowerThirds': True,
                'customLowerThirds': [{'label': 'Guest', 'content': 'Dr. Smith'}],
            },
        }

        response = app.test_client().post('/api/wizard_export', json=payload)

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True) if response.status_code != 200 else '')
        self.assertEqual(response.mimetype, 'application/zip')
        self.assertIn('service_package_2026-09-29.zip', response.headers['Content-Disposition'])
        folder = '2026-09-29/'
        with zipfile.ZipFile(io.BytesIO(response.data)) as package:
            self.assertIsNone(package.testzip())
            expected = {
                'title_cards/Title_Card.png',
                'title_cards/Custom_Title_Card.png',
                'lower_thirds/First_Reading.png',
                'lower_thirds/BLANK_TEMPLATE.png',
                'lower_thirds/Custom_01_Guest.png',
                'readings/First_Reading.txt',
                'readings/First_Reading_Reference.txt',
                'service_details/Opening_Hymn.png',
                'announcements/Announcement_1_Parish picnic.png',
                'service_order/Order_01_Opening hymn.png',
                'countdown/Countdown_05min.png',
                'Package_Summary.txt',
            }
            self.assertTrue({folder + name for name in expected} <= set(package.namelist()))
            summary = package.read(folder + 'Package_Summary.txt').decode('utf-8')
            self.assertIn('Celebration: St. Michael and All Angels', summary)
            self.assertTrue(package.read(folder + 'title_cards/Title_Card.png').startswith(b'\x89PNG'))


if __name__ == '__main__':
    unittest.main()
