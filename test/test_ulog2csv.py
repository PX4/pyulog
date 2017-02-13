import os
import inspect
import unittest
from pyulog import ulog2csv, info, params, messages, extract_gps_dump
import sys
import tempfile
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

class Test(unittest.TestCase):

    def run_against_file(self, expected_output_file, test):
        """
        run a test and compare the output against an expected file
        """
        saved_stdout = sys.stdout
        with open(expected_output_file, 'r') as file_handle:
            expected_output = file_handle.read().strip()
            try:
                out = StringIO()
                sys.stdout = out
                test()
                output = out.getvalue().strip()
                assert output == expected_output
            finally:
                sys.stdout = saved_stdout
                print("Got output:")
                print(output)
                print("\nExpected output:")
                print(expected_output)

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
        self.run_against_file(
                os.path.join(TEST_PATH, 'sample_info.txt'), info.main)

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
        self.run_against_file(
                os.path.join(TEST_PATH, 'sample_messages.txt'), messages.main)

    def test_params_cli(self):
        sys.argv = [
            '',
            os.path.join(TEST_PATH, 'sample.ulg')
        ]
        self.run_against_file(
                os.path.join(TEST_PATH, 'sample_params.txt'), params.main)


# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4 : 
