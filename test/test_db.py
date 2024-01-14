'''
Test the DatabaseULog module.
'''

import unittest
import os
from unittest.mock import patch
import numpy as np
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
            db_dataset = next(ds for ds in dbulog_loaded.data_list
                              if ds.name == dataset.name and ds.multi_id == dataset.multi_id)
            self.assertEqual(len(db_dataset.data), 0)
            self.assertNotEqual(len(dataset.data), 0)
            ulog_dataset = ulog.get_dataset(dataset.name,
                                            multi_instance=dataset.multi_id)
            dbulog_dataset = dbulog_loaded.get_dataset(dataset.name,
                                                       multi_instance=dataset.multi_id)
            self.assertEqual(ulog_dataset, dbulog_dataset)


    def test_data_caching(self):
        '''
        Verify that the caching of dataset data works as expected.
        '''
        test_file = os.path.join(TEST_PATH, 'sample_log_small.ulg')

        dbulog_saved = DatabaseULog(self.db_handle, log_file=test_file)
        dbulog_saved.save()
        primary_key = dbulog_saved.primary_key
        dbulog_loaded = DatabaseULog(self.db_handle, primary_key=primary_key, lazy=True)
        for dataset in dbulog_loaded.data_list:
            cache_miss = dbulog_loaded.get_dataset(dataset.name,
                                                   multi_instance=dataset.multi_id,
                                                   caching=True)
            cache_hit = dbulog_loaded.get_dataset(dataset.name,
                                                  multi_instance=dataset.multi_id,
                                                  caching=True)
            uncached = dbulog_loaded.get_dataset(dataset.name,
                                                 multi_instance=dataset.multi_id,
                                                 caching=False)

            self.assertEqual(cache_miss, cache_hit)
            self.assertEqual(cache_miss, uncached)
            self.assertIs(cache_miss, cache_hit)
            self.assertIsNot(cache_miss, uncached)

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

    @data('sample_log_small')
    def test_sha256sum(self, test_case):
        '''
        Verify that the sha256sum set on save can be used to find the same file again.
        '''

        test_file = os.path.join(TEST_PATH, f'{test_case}.ulg')
        dbulog = DatabaseULog(self.db_handle, log_file=test_file)
        dbulog.save()
        digest = DatabaseULog.calc_sha256sum(test_file)
        self.assertEqual(digest, dbulog.sha256sum)

        pk_from_digest = DatabaseULog.primary_key_from_sha256sum(self.db_handle, digest)
        self.assertEqual(pk_from_digest, dbulog.primary_key)

        dbulog_duplicate = DatabaseULog(self.db_handle, log_file=test_file)
        with self.assertRaises(KeyError):
            dbulog_duplicate.save()

    def test_delete(self):
        '''
        Verify that the delete method completely deletes the relevant ulog from
        the database, and nothing else, by looking at the size of the database
        before and after deleting.
        '''

        def db_size():
            '''
            Get the size in bytes of the database file, after VACUUMING to make
            sure that deleted rows are cleaned up.
            '''
            with self.db_handle() as con:
                con.execute('VACUUM')
            return os.path.getsize(self.db_path)

        # We pre-populate the database with a log to detect if delete() just
        # wipes everything
        test_file1 = os.path.join(TEST_PATH, 'sample.ulg')
        DatabaseULog(self.db_handle, log_file=test_file1).save()
        initial_size = db_size()

        test_file2 = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        dbulog = DatabaseULog(self.db_handle, log_file=test_file2)
        dbulog.save()
        self.assertNotEqual(db_size(), initial_size)

        dbulog.delete()
        self.assertEqual(db_size(), initial_size)

    def test_json(self):
        '''
        Verify that the storage of JSON rows allows for reproduction of the
        datasets.
        '''
        test_file = os.path.join(TEST_PATH, 'sample_log_small.ulg')
        log_path = os.path.join(TEST_PATH, test_file)

        dbulog = DatabaseULog(self.db_handle, log_file=log_path)
        dbulog.save(append_json=True)

        with self.db_handle() as con:
            cur = con.cursor()
            for dataset in dbulog.data_list:
                for field_name, values in dataset.data.items():
                    cur.execute('''
                        SELECT j.key, j.value
                        FROM ULogField uf, json_each(uf.ValueJson) j
                            JOIN ULogDataset uds ON uf.DatasetId = uds.Id
                        WHERE uds.DatasetName = ?
                            AND uds.MultiId = ?
                            AND uf.TopicName = ?
                            AND uds.ULogId = ?
                        ORDER BY j.key ASC
                    ''', (dataset.name, dataset.multi_id, field_name, dbulog.primary_key))
                    results = np.array(cur.fetchall(), dtype=float)
                    db_timestamps = results[:,0].flatten()
                    db_values = results[:,1].flatten()

                    # We must filter out None, nan and inf values since JSON
                    # doesn't support nan and inf.
                    db_values_finite = db_values[np.isfinite(db_values)]
                    values_finite = values[np.isfinite(values)]

                    # We test for approximate equality since we are comparing
                    # string-formatted floats.
                    self.assertEqual(len(db_values_finite), len(values_finite))
                    if len(db_values_finite) > 0:
                        np.testing.assert_allclose(db_values_finite, values_finite)

                    if field_name == 'timestamp':
                        self.assertEqual(len(db_timestamps), len(values))
                        np.testing.assert_allclose(db_timestamps, values)
            cur.close()
