'''
Tests the ULog class
'''

import os
import inspect
import unittest
import tempfile

from ddt import ddt, data

import pyulog

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestULog(unittest.TestCase):
    '''
    Tests the ULog class
    '''

    @data('sample')
    def test_comparison(self, base_name):
        '''
        Test that the custom comparison method works as expected.
        '''
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        ulog1 = pyulog.ULog(ulog_file_name)
        ulog2 = pyulog.ULog(ulog_file_name)
        assert ulog1 == ulog2
        assert ulog1 is not ulog2

        # make them different in arbitrary field
        ulog1.data_list[0].data['timestamp'][0] += 1
        assert ulog1 != ulog2


    @data('sample',
          'sample_appended',
          'sample_appended_multiple',
          'sample_logging_tagged_and_default_params')
    def test_write_ulog(self, base_name):
        '''
        Test that the write_ulog method successfully replicates all relevant data.
        '''
        with tempfile.TemporaryDirectory() as tmpdirname:
            ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
            written_ulog_file_name = os.path.join(tmpdirname, base_name + '_copy.ulg')

            original = pyulog.ULog(ulog_file_name)
            original.write_ulog(written_ulog_file_name)
            copied = pyulog.ULog(written_ulog_file_name)

        # Some fields are not copied but dropped, so we cheat by modifying the original
        original._sync_seq_cnt = 0  # pylint: disable=protected-access
        original._appended_offsets = []  # pylint: disable=protected-access
        original._incompat_flags[0] &= 0xFE  # pylint: disable=protected-access

        assert copied == original

# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4
