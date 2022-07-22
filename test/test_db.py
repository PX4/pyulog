'''
Test that the database module works correctly.
'''

import unittest
import os
import inspect
from functools import partial
import numpy as np
from ddt import ddt, data

from pyulog import ULog
from pyulog.db import DatabaseULog

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestDatabaseULog(unittest.TestCase):
    '''
    Test that the DatabaseULog successfully reads a ULog, builds a database and
    then is able to read from it without losing any data.
    '''

    @classmethod
    def setUpClass(cls):
        '''
        Set up the test database.
        '''
        db_setup_script = os.path.join(TEST_PATH, '../pyulog/sql/setup_db.sql')
        TestDatabaseULog.db_path = os.path.join(TEST_PATH, 'pyulog_test.sqlite3')
        TestDatabaseULog.db_handle = DatabaseULog.get_db_handle(TestDatabaseULog.db_path)
        with open(db_setup_script, 'r', encoding='utf8') as setup_file:
            setup_sql = setup_file.read()
        with TestDatabaseULog.db_handle() as con:
            cur = con.cursor()
            cur.executescript(setup_sql)
            cur.close()

    @classmethod
    def tearDownClass(cls):
        '''
        Remove the test database after use.
        '''
        os.remove(TestDatabaseULog.db_path)

    @data('sample_log_small',
          'sample_appended_multiple',
          'sample_appended',
          'sample',
          'sample_logging_tagged_and_default_params')
    def test_parsing(self, test_case):
        ''' Verify that log files written and read from the database are
        identical to the original ulog file. '''
        test_file = os.path.join(TEST_PATH, f'{test_case}.ulg')
        log_path = os.path.join(TEST_PATH, test_file)

        ulog = ULog(log_path)
        dbulog = DatabaseULog(TestDatabaseULog.db_handle, log_file=test_file)
        dbulog.save()
        primary_key = dbulog.primary_key
        del dbulog
        dbulog = DatabaseULog(TestDatabaseULog.db_handle, primary_key=primary_key, lazy=False)
        for ulog_key, ulog_value in ulog.__dict__.items():
            self.assertEqual(ulog_value, getattr(dbulog, ulog_key))

    def test_save(self):
        ''' Test that save() twice raises an error.'''
        log_path = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        ulog = ULog(log_path)
        dbulog = DatabaseULog(TestDatabaseULog.db_handle, log_file=log_path)
        dbulog.save()
        with self.assertRaises(KeyError):
            dbulog.save()

    def test_load(self):
        ''' Test that load() on an unknown pk raises an error.'''
        with self.assertRaises(KeyError):
            _ = DatabaseULog(TestDatabaseULog.db_handle, primary_key=100)
