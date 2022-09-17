'''
Test the DatabaseULog module.
'''

import unittest
import os
from unittest.mock import patch
from ddt import ddt, data

from pyulog import ULog
from pyulog.db import DatabaseULog
from pyulog.migrate_db import migrate_db

TEST_PATH = os.path.dirname(os.path.abspath(__file__))

@ddt
class TestDatabaseULog(unittest.TestCase):
    '''
    Test that the DatabaseULog successfully reads a ULog, writes it to database
    and then is able to read from it without losing any data.
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

    @data('sample_log_small',
          'sample_appended_multiple',
          'sample_appended',
          'sample',
          'sample_logging_tagged_and_default_params')
    def test_parsing(self, test_case):
        '''
        Verify that log files written and read from the database are
        identical to the original ulog file.
        '''
        test_file = os.path.join(TEST_PATH, f'{test_case}.ulg')
        log_path = os.path.join(TEST_PATH, test_file)

        ulog = ULog(log_path)
        dbulog_saved = DatabaseULog(self.db_handle, log_file=test_file)
        dbulog_saved.save()
        primary_key = dbulog_saved.primary_key
        dbulog_loaded = DatabaseULog(self.db_handle, primary_key=primary_key, lazy=False)
        for ulog_key, ulog_value in ulog.__dict__.items():
            self.assertEqual(ulog_value, getattr(dbulog_loaded, ulog_key))

    def test_lazy(self):
        '''
        Verify that when lazy loading is enabled (which is the default
        behaviour), then the datasets are only retrieved when get_dataset is
        explicitly called.
        '''
        test_file = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        log_path = os.path.join(TEST_PATH, test_file)

        ulog = ULog(log_path)
        dbulog_saved = DatabaseULog(self.db_handle, log_file=test_file)
        dbulog_saved.save()
        primary_key = dbulog_saved.primary_key
        dbulog_loaded = DatabaseULog(self.db_handle, primary_key=primary_key)
        for dataset in ulog.data_list:
            db_dataset = next(ds for ds in dbulog_loaded.data_list if ds.name == dataset.name)
            self.assertEqual(len(db_dataset.data), 0)
            self.assertNotEqual(len(dataset.data), 0)
            self.assertEqual(ulog.get_dataset(dataset.name),
                             dbulog_loaded.get_dataset(dataset.name))

    def test_save(self):
        '''
        Test that save() twice raises an error, since we currently do not
        support updating the database.
        '''
        log_path = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        dbulog = DatabaseULog(self.db_handle, log_file=log_path)
        dbulog.save()
        with self.assertRaises(KeyError):
            dbulog.save()

    def test_load(self):
        ''' Test that load() on an unknown primary key raises an error.'''
        with self.assertRaises(KeyError):
            _ = DatabaseULog(self.db_handle, primary_key=100)

    def test_unapplied_migrations(self):
        '''
        Test that we get get an error when trying to initialize a DatabaseULog
        if there are unapplied migrations, i.e. the SCHEMA_VERSION of
        DatabaseULog is larger than user_version in the database.
        '''
        migrate_db(self.db_path)
        log_file = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        _ = DatabaseULog(self.db_handle, log_file=log_file)
        with self.assertRaises(ValueError):
            # Increment SCHEMA_VERSION so the database is seemingly out of date
            with patch.object(DatabaseULog, 'SCHEMA_VERSION', DatabaseULog.SCHEMA_VERSION+1):
                _ = DatabaseULog(self.db_handle, log_file=log_file)
