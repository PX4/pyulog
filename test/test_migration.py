'''
Test that the migration module works correctly.
'''

import unittest
import os
import re
import sqlite3
import subprocess

from unittest.mock import patch
from ddt import ddt, data
from pyulog.db import DatabaseULog
from pyulog.migrate_db import migrate_db

TEST_PATH = os.path.dirname(os.path.abspath(__file__))

@ddt
class TestMigration(unittest.TestCase):
    '''
    Using both fake and real migration files, try various migration sequences
    and check that the state of the database is as expected from the migrations
    that were run.

    '''

    def setUp(self):
        '''
        Set up the test database and fake migration script directory for each test.
        '''
        self.db_path = os.path.join(TEST_PATH, 'test_pyulog.sqlite3')
        self.db_handle = DatabaseULog.get_db_handle(self.db_path)
        self.sql_dir = os.path.join(TEST_PATH, 'test_sql')
        os.mkdir(self.sql_dir)

    def tearDown(self):
        '''
        Remove test database and fake migration script directory after each test.
        '''
        for filename in os.listdir(self.sql_dir):
            assert re.match(r'pyulog\.\d\.sql', filename), 'Only removing migration files.'
            filepath = os.path.join(self.sql_dir, filename)
            os.remove(filepath)
        os.rmdir(self.sql_dir)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _make_migration_file(self, sql):
        '''
        Utility function for creating fake migration files. This is necessary
        because the migration tool reads from disk, so any fake migration
        scripts we want to test must be written to disk too, with correct file
        names.

        The files are cleaned up in tearDown.
        '''
        current_migration_files = os.listdir(self.sql_dir)
        migration_index = len(current_migration_files) + 1
        sql_filename = f'pyulog.{migration_index}.sql'
        sql_path = os.path.join(self.sql_dir, sql_filename)
        with open(sql_path, 'w', encoding='utf8') as migration_file:
            migration_file.write(sql)

    def _get_db_info(self):
        '''
        Utility function for getting the current database version and column
        names. This is used to verify the state of the database after running
        various migration scripts.
        '''
        with self.db_handle() as con:
            cur = con.cursor()
            cur.execute('PRAGMA table_info(TestTable)')
            table_info = cur.fetchall()
            cur.execute('PRAGMA user_version')
            (db_version,) = cur.fetchone()
            cur.close()
        return db_version, [column_info[1] for column_info in table_info]

    def test_good_migrations(self):
        '''
        Test that two sequential migrations run successfully and sequentially.
        '''
        self._make_migration_file('BEGIN; CREATE TABLE TestTable ( Id INTEGER ); COMMIT;')
        with patch.object(DatabaseULog, 'SCHEMA_VERSION', 1):
            migrate_db(self.db_path, sql_dir=self.sql_dir)
        db_version, col_names = self._get_db_info()
        self.assertEqual(col_names[0], 'Id')
        self.assertEqual(db_version, 1)

        self._make_migration_file('BEGIN; ALTER TABLE TestTable RENAME Id to IdRenamed; COMMIT;')
        with patch.object(DatabaseULog, 'SCHEMA_VERSION', 2):
            migrate_db(self.db_path, sql_dir=self.sql_dir)
        db_version, col_names = self._get_db_info()
        self.assertEqual(col_names[0], 'IdRenamed')
        self.assertEqual(db_version, 2)

    @data('CREATE TABLE TestTable;',
          'BEGIN; CREATE TABLE TestTable;',
          'CREATE TABLE TestTable;  END;')
    def test_transactions(self, sql_line):
        '''
        Verify that migration files are rejected if they don't enforce
        transactions correctly.
        '''
        self._make_migration_file(sql_line)
        with self.assertRaises(ValueError), \
            patch.object(DatabaseULog, 'SCHEMA_VERSION', 1):
            migrate_db(self.db_path, sql_dir=self.sql_dir)

    def test_bad_migrations(self):
        '''
        Insert a bug into a line of a migration script, and verify that the
        script is rolled back.
        '''
        self._make_migration_file('''
BEGIN;
CREATE TABLE TestTable ( Id INTEGER, Value TEXT );
COMMIT;
        ''')
        self._make_migration_file('''
BEGIN;
ALTER TABLE TestTable RENAME COLUMN Id TO IdRenamed;
ALTER TABLE TestTable RENAME <BUG>COLUMN IdRenamed TO IdRenamed2;
ALTER TABLE TestTable RENAME COLUMN Value TO ValueRenamed;
COMMIT;
        ''')
        with self.assertRaises(sqlite3.OperationalError), \
             patch.object(DatabaseULog, 'SCHEMA_VERSION', 2):
            migrate_db(self.db_path, sql_dir=self.sql_dir)
        db_version, col_names = self._get_db_info()
        self.assertEqual(col_names[0], 'Id')
        # Also check the 'Value' column, since the renaming of that field would
        # not have been impacted by the buggy line.
        self.assertEqual(col_names[1], 'Value')
        self.assertEqual(db_version, 1)

    def test_existing_db(self):
        '''
        Verify that the migration tool will not modify databases that are were
        created before the migration tool. Then verify that the -f flag
        correctly forces the execution anyway.
        '''
        db_version, _ = self._get_db_info()  # This function implicitly creates the database
        self.assertEqual(db_version, 0)
        with self.assertRaises(FileExistsError):
            migrate_db(self.db_path)

        migrate_db(self.db_path, force=True)
        db_version, _ = self._get_db_info()
        self.assertEqual(db_version, DatabaseULog.SCHEMA_VERSION)

    def test_missing_migration_file(self):
        '''
        Verify that the migration tool stops after it encounters a non-existent
        migration file.
        '''
        self._make_migration_file('BEGIN; CREATE TABLE TestTable ( Id INTEGER ); COMMIT;')
        with self.assertRaises(FileNotFoundError), \
             patch.object(DatabaseULog, 'SCHEMA_VERSION', 2):
            migrate_db(self.db_path, sql_dir=self.sql_dir)
        db_version, col_names = self._get_db_info()
        self.assertEqual(col_names[0], 'Id')
        self.assertEqual(db_version, 1)

    def test_noop(self):
        '''
        Verify that the noop flag removes any effect on the database.
        '''
        migrate_db(self.db_path, noop=True)
        db_version, _ = self._get_db_info()
        self.assertEqual(db_version, 0)

    def test_real_migrations(self):
        '''
        Verify that the migration scripts in the pyulog/sql directory execute
        successfully.
        '''
        migrate_db(self.db_path)
        db_version, _ = self._get_db_info()
        self.assertEqual(db_version, DatabaseULog.SCHEMA_VERSION)

    def test_cli(self):
        '''
        Verify that the command line tol ulog_migratedb completes the
        migrations successfully.
        '''
        result = subprocess.run(['ulog_migratedb', '-d', self.db_path], check=True)
        self.assertEqual(result.returncode, 0)
        db_version, _ = self._get_db_info()
        self.assertEqual(db_version, DatabaseULog.SCHEMA_VERSION)
