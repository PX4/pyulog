'''
Test extract_message module
'''

import os
import inspect
import unittest

from ddt import ddt, data

from pyulog.extract_message import extract_message

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestExtractMessage(unittest.TestCase):
    """
    Test extract_message module.
    """

    @data('sample')
    def test_extract_message(self, test_case):
        """
        Test that extract_message module runs without error.
        """

        ulog_file_name = os.path.join(TEST_PATH, test_case+'.ulg')
        message = "actuator_controls_0"
        time_s = None
        time_e = None
        extract_message(ulog_file_name,
                        message,
                        time_s,
                        time_e)

# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4
