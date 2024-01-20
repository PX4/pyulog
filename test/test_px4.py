'''
Tests the PX4ULog class
'''

import os
import inspect
import unittest

from ddt import ddt, data

from pyulog import ULog
from pyulog.px4 import PX4ULog
from pyulog.db import DatabaseULog
from pyulog.migrate_db import migrate_db

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestPX4ULog(unittest.TestCase):
    '''
    Tests the PX4ULog class
    '''

    def setUp(self):
        '''
        Set up the test database.
        '''
        self.db_path = os.path.join(TEST_PATH, 'pyulog_test.sqlite3')
        self.db_handle = DatabaseULog.get_db_handle(self.db_path)
        migrate_db(self.db_path)


    def tearDown(self):
        '''
        Remove the test database after use.
        '''
        os.remove(self.db_path)

    @data('sample',
          'sample_appended',
          'sample_appended_multiple',
          'sample_logging_tagged_and_default_params')
    def test_add_roll_pitch_yaw(self, base_name):
        '''
        Test that add_roll_pitch_yaw correctly adds RPY values to 'vehicle_attitude'
        '''
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        ulog = ULog(ulog_file_name)
        px4 = PX4ULog(ulog)
        px4.add_roll_pitch_yaw()

        dataset = ulog.get_dataset('vehicle_attitude')
        assert 'roll' in dataset.data
        assert 'pitch' in dataset.data
        assert 'yaw' in dataset.data

    @data('sample',
          'sample_appended',
          'sample_appended_multiple',
          'sample_logging_tagged_and_default_params')
    def test_add_roll_pitch_yaw_db(self, base_name):
        '''
        Test that add_roll_pitch_yaw correctly adds RPY values to
        'vehicle_attitude' on a DatabaseULog object.
        '''
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        dbulog = DatabaseULog(self.db_handle, log_file=ulog_file_name)
        dbulog.save()
        del dbulog
        digest = DatabaseULog.calc_sha256sum(ulog_file_name)
        primary_key = DatabaseULog.primary_key_from_sha256sum(self.db_handle, digest)
        dbulog = DatabaseULog(self.db_handle, primary_key=primary_key, lazy=False)
        px4 = PX4ULog(dbulog)
        px4.add_roll_pitch_yaw()

        dataset = dbulog.get_dataset('vehicle_attitude')
        assert 'roll' in dataset.data
        assert 'pitch' in dataset.data
        assert 'yaw' in dataset.data


# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4
