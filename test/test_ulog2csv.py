import os
import inspect
import unittest
from pyulog import ulog2csv, info, params, messages, extract_gps_dump
import sys
import tempfile

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

class Test(unittest.TestCase):

    def test_ulog2csv(self):
        tmpdir = tempfile.gettempdir()
        print('writing files to ', tmpdir)
        ulog_file_name = os.path.join(TEST_PATH, 'sample.ulg')
        messages = []
        output=tmpdir
        delimiter=','
        ulog2csv.convert_ulog2csv(ulog_file_name, messages, output, delimiter)

    def test_pyulog_info_cli(self):
        sys.argv = [
            '',
            os.path.join(TEST_PATH, 'sample.ulg')
        ]
        info.main()

    @unittest.skip("no gps data in log file")
    def test_extract_gps_dump_cli(self):
        sys.argv = [
            '',
            os.path.join(TEST_PATH, 'sample.ulg')
        ]
        extract_gps_dump.main()

    def test_messages_cli(self):
        sys.argv = [
            '',
            os.path.join(TEST_PATH, 'sample.ulg')
        ]
        messages.main()

    def test_params_cli(self):
        sys.argv = [
            '',
            os.path.join(TEST_PATH, 'sample.ulg')
        ]
        params.main()


# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4 : 
