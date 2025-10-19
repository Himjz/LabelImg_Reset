#!/usr/bin/env python
import os
import sys
import unittest
import tempfile
from pathlib import Path

__author__ = 'TzuTaLin'

current_script_path = Path(__file__).resolve()
current_dir = current_script_path.parent

libs_path = (current_dir.parent / "libs").resolve()
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from libs.settings import Settings


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.temp_path = self.temp_file.name
        self.settings = Settings()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_key_operations(self):
        self.settings['test0'] = 'hello'
        self.settings['test1'] = 10
        self.settings['test2'] = [0, 2, 3]

        self.assertEqual(self.settings.get('test0'), 'hello')
        self.assertEqual(self.settings['test1'], 10)
        self.assertEqual(self.settings.get('test2'), [0, 2, 3])

        self.assertEqual(self.settings.get('test3', 3), 3)
        self.assertIsNone(self.settings.get('test4'))

    def test_save_and_load(self):
        test_data = {
            'str_val': 'world',
            'int_val': 20,
            'list_val': [1, 3, 5]
        }
        for key, value in test_data.items():
            self.settings[key] = value

        self.assertTrue(self.settings.save())

        new_settings = Settings()
        new_settings.load()

        for key, expected in test_data.items():
            self.assertEqual(new_settings.get(key), expected)

    def test_reset(self):
        self.settings['test0'] = 'hello'
        self.settings['test1'] = 10
        self.settings.save()

        self.settings.reset()

        self.assertIsNone(self.settings.get('test0'))
        self.assertIsNone(self.settings.get('test1'))

        self.settings.save()
        new_settings = Settings()
        new_settings.load()
        self.assertIsNone(new_settings.get('test0'))


if __name__ == '__main__':
    unittest.main(verbosity=2)