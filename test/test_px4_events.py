"""
Tests the PX4Events class
"""

import os
import inspect
import unittest

from ddt import ddt, data

import pyulog
from pyulog.px4_events import PX4Events

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestPX4Events(unittest.TestCase):
    """
    Tests the PX4Events class
    """

    @data('sample_px4_events')
    def test_px4_events(self, base_name):
        """
        Test that the PX4 events are extracted.
        """
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        ulog = pyulog.ULog(ulog_file_name)
        px4_ulog = PX4Events()

        def default_json_definitions_cb(already_has_default_parser: bool):
            raise AssertionError('Must use definitions from logs')
        px4_ulog.set_default_json_definitions_cb(default_json_definitions_cb)

        messages = px4_ulog.get_logged_events(ulog)
        expected_messages = [
            (1710773350346000, 'INFO', 'logging: opening log file 2024-3-18/14_49_10.ulg'),
            (1710773365282000, 'INFO', 'Armed by internal command'),
            (1710773365282000, 'INFO', 'Using default takeoff altitude: 2.50 m'),
            (1710773367094000, 'INFO', 'Takeoff detected'),
            (1710773372482000, 'INFO', 'RTL: start return at 491 m (3 m above destination)'),
            (1710773372694000, 'INFO', 'RTL: land at destination'),
            (1710773378482000, 'INFO', 'Landing detected'),
            (1710773380486000, 'INFO', 'Disarmed by landing')
        ]
        assert messages == expected_messages
