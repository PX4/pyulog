'''
Tool for handling changes in the database schema. This is necessary for
avoiding breaking backwards compatibility whenver bugs are discovered in the
database model, or if the ULog format changes.

There are some options available, such as "alembic" or "migrations', but these
seem like overkill for us. For instance, we don't really need to migrate both up and
down, just up.
'''

import os
import argparse
from pyulog.db import DatabaseULog

def main():
    '''
    Entry point for the console script.
    '''
    parser = argparse.ArgumentParser(description='Setup the database for DatabaseULog')
    parser.add_argument('-d', '--database', dest='db_path', action='store',
                        help='Path to the database file',
                        default='pyulog.sqlite3')
    # The noop flag actually has a side effect if it is called on an uncreated
    # database, since the "PRAGMA user_version" command implicitly creates the
    # database. The created database will have user_version = 0, which will
    # later confuse the migration tool. however, this edge case will mostly be
    # relevant for advanced users, and can be handled with the -f flag.
    parser.add_argument('-n', '--noop', dest='noop', action='store_true',
                        help='Only print results, do not execute migration scripts.',
                        default=False)
    parser.add_argument('-s', '--sql', dest='sql_dir', action='store',
                        help='Directory with migration SQL files',
                        default=None)
    parser.add_argument('-f', '--force', dest='force', action='store_true',
                        help=('Run the migration script even if the database is not created'
                              'with this script.'),
                        default=False)
    args = parser.parse_args()
    migrate_db(args.db_path, sql_dir=args.sql_dir, noop=args.noop, force=args.force)

def _read_db_schema_version(db_path, force):
    '''
    Read and validate the schema version defined by the "PRAGMA user_version"
    field in the database. If the database file exists and schema version is 0,
    then this means that the database was not created with the migration tool.
    This means that the database is in a state unknown to the migration tool,
    and hence a migration could cause schema corruption. The default behavior
    in this case is to reject the migration, but it can be overriden with
    force=True.
    '''
    db_handle = DatabaseULog.get_db_handle(db_path)
    if not os.path.isfile(db_path):
        print(f'Database file {db_path} not found, creating it from scratch.')
        return 0
    print(f'Found database file {db_path}.')

    with db_handle() as con:
        cur = con.cursor()
        cur.execute('PRAGMA user_version')
        (db_schema_version,) = cur.fetchone()
        cur.close()

    if db_schema_version is None:
        raise ValueError(f'Could not fetch database schema version for {db_path}.')
    if db_schema_version == 0 and not force:
        raise FileExistsError('Database has user_version = 0, rejecting migration.'
                              'Use the "force" flag to migrate anyway.')
    if not isinstance(db_schema_version, int) or db_schema_version < 0:
        raise ValueError(f'Invalid database schema version {db_schema_version}.')
    return db_schema_version

def _read_migration_file(migration_id, sql_dir):
    '''
    Read the migration file with id "migration_id" in directory "sql_dir", and
    check that it handles transactions strictly.
    '''
    migration_filename_format = os.path.join(sql_dir, 'pyulog.{migration_id}.sql')
    migration_filename = migration_filename_format.format(migration_id=migration_id)
    if not os.path.exists(migration_filename):
        raise FileNotFoundError(f'Migration file {migration_filename} does not exist. '
                                f'Stopped after migration {migration_id}.')

    with open(migration_filename, 'r', encoding='utf8') as migration_file:
        migration_lines = migration_file.read()
    if not migration_lines.strip().startswith('BEGIN;'):
        raise ValueError(f'Migration file {migration_filename} must start with "BEGIN;"')
    if not migration_lines.strip().endswith('COMMIT;'):
        raise ValueError(f'Migration file {migration_filename} must end with "COMMIT;"')

    migration_lines +=  f'\nPRAGMA user_version = {migration_id};'
    return migration_filename, migration_lines

def migrate_db(db_path, sql_dir=None, noop=False, force=False):
    '''
    Apply database migrations that have not yet been applied.

    Compares "PRAGMA user_version" from the sqlite3 database at "db_path" with
    the SCHEMA_VERSION in the DatabaseULog class. If the former is larger than
    the latter, then migration scripts will be read and executed from files in
    "sql_dir", and the user_version will be incremented, until the database is
    up to date.
    '''
    if sql_dir is None:
        module_dir = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
        sql_dir = os.path.join(module_dir, 'sql')
    if not os.path.isdir(sql_dir):
        raise NotADirectoryError(f'{sql_dir} is not a directory.')
    print(f'Using migration files in {sql_dir}.')

    db_schema_version = _read_db_schema_version(db_path, force)
    class_schema_version = DatabaseULog.SCHEMA_VERSION
    print('Current schema version: {} (database) and {} (code).'.format(
        db_schema_version,
        class_schema_version,
    ))

    db_handle = DatabaseULog.get_db_handle(db_path)
    with db_handle() as con:
        cur = con.cursor()
        for migration_id in range(db_schema_version+1,
                                  DatabaseULog.SCHEMA_VERSION+1):
            migration_filename, migration_lines = _read_migration_file(migration_id, sql_dir)
            print(f'Executing {migration_filename}.')
            if noop:
                print(migration_lines)
            else:
                cur.executescript(migration_lines)

        cur.close()
        print('Migration done.')
    return db_path

if __name__ == '__main__':
    raise SystemExit(main())
