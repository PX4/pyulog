BEGIN;
PRAGMA foreign_keys=off;

CREATE TABLE IF NOT EXISTS ULog_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SHA256Sum TEXT UNIQUE,
        FileVersion INT,
        StartTimestamp REAL,
        LastTimestamp REAL,
        CompatFlags TEXT,
        IncompatFlags TEXT,
        SyncCount INT,
        HasSync BOOLEAN
);
INSERT OR IGNORE INTO ULog_tmp (Id, FileVersion, StartTimestamp, LastTimestamp, CompatFlags, IncompatFlags, SyncCount, HasSync) SELECT Id, FileVersion, StartTimestamp, LastTimestamp, CompatFlags, IncompatFlags, SyncCount, HasSync FROM ULog;


CREATE TABLE IF NOT EXISTS ULogAppendedOffsets_tmp (
        SeriesIndex INTEGER,
        Offset INTEGER,
        ULogId INT REFERENCES ULog_tmp (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogAppendedOffsets_tmp SELECT * FROM ULogAppendedOffsets;

CREATE TABLE IF NOT EXISTS ULogDataset_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        DatasetName TEXT,
        MultiId INT,
        MessageId INT,
        TimestampIndex INT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE,
        UNIQUE (ULogId, DatasetName, MultiId)
);
INSERT OR IGNORE INTO ULogDataset_tmp SELECT * FROM ULogDataset;

CREATE TABLE IF NOT EXISTS ULogField_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        TopicName TEXT,
        DataType TEXT,
        ValueArray BLOB,
        DatasetId INTEGER REFERENCES ULogDataset (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogField_tmp SELECT * FROM ULogField;
CREATE INDEX IF NOT EXISTS btree_ulogfield_datasetid ON ULogField_tmp(DatasetId);

CREATE TABLE IF NOT EXISTS ULogMessageDropout_tmp (
        Timestamp REAL,
        Duration FLOAT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageDropout_tmp SELECT * FROM ULogMessageDropout;

CREATE TABLE IF NOT EXISTS ULogMessageFormat_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageFormat_tmp SELECT * FROM ULogMessageFormat;

CREATE TABLE IF NOT EXISTS ULogMessageFormatField_tmp (
        FieldType TEXT,
        ArraySize INT,
        Name TEXT,
        MessageId INT REFERENCES ULogMessageFormat (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageFormatField_tmp SELECT * FROM ULogMessageFormatField;

CREATE TABLE IF NOT EXISTS ULogMessageLogging_tmp (
        LogLevel INT,
        Timestamp REAL,
        Message TEXT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageLogging_tmp SELECT * FROM ULogMessageLogging;

CREATE TABLE IF NOT EXISTS ULogMessageLoggingTagged_tmp (
        LogLevel INT,
        Timestamp REAL,
        Tag INT,
        Message TEXT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageLoggingTagged_tmp SELECT * FROM ULogMessageLoggingTagged;

CREATE TABLE IF NOT EXISTS ULogMessageInfo_tmp (
        Key TEXT,
        Typename TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageInfo_tmp SELECT * FROM ULogMessageInfo;

CREATE TABLE IF NOT EXISTS ULogMessageInfoMultiple_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Key TEXT,
        Typename TEXT,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageInfoMultiple_tmp SELECT * FROM ULogMessageInfoMultiple;

CREATE TABLE IF NOT EXISTS ULogMessageInfoMultipleList_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SeriesIndex INTEGER,
        MessageId TEXT REFERENCES ULogMessageInfoMultiple (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageInfoMultipleList_tmp SELECT * FROM ULogMessageInfoMultipleList;

CREATE TABLE IF NOT EXISTS ULogMessageInfoMultipleListElement_tmp (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SeriesIndex INTEGER,
        Value TEXT,
        ListId TEXT REFERENCES ULogMessageInfoMultipleList (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogMessageInfoMultipleListElement_tmp SELECT * FROM ULogMessageInfoMultipleListElement;

CREATE TABLE IF NOT EXISTS ULogInitialParameter_tmp (
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogInitialParameter_tmp SELECT * FROM ULogInitialParameter;

CREATE TABLE IF NOT EXISTS ULogChangedParameter_tmp (
        Timestamp REAL,
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogChangedParameter_tmp SELECT * FROM ULogChangedParameter;

CREATE TABLE IF NOT EXISTS ULogDefaultParameter_tmp (
        DefaultType INT,
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id) ON DELETE CASCADE
);
INSERT OR IGNORE INTO ULogDefaultParameter_tmp SELECT * FROM ULogDefaultParameter;

DROP TABLE IF EXISTS ULog;
DROP TABLE IF EXISTS ULogAppendedOffsets;
DROP TABLE IF EXISTS ULogDataset;
DROP TABLE IF EXISTS ULogField;
DROP TABLE IF EXISTS ULogMessageDropout;
DROP TABLE IF EXISTS ULogMessageFormat;
DROP TABLE IF EXISTS ULogMessageFormatField;
DROP TABLE IF EXISTS ULogMessageLogging;
DROP TABLE IF EXISTS ULogMessageLoggingTagged;
DROP TABLE IF EXISTS ULogMessageInfo;
DROP TABLE IF EXISTS ULogMessageInfoMultiple;
DROP TABLE IF EXISTS ULogMessageInfoMultipleList;
DROP TABLE IF EXISTS ULogMessageInfoMultipleListElement;
DROP TABLE IF EXISTS ULogInitialParameter;
DROP TABLE IF EXISTS ULogChangedParameter;
DROP TABLE IF EXISTS ULogDefaultParameter;

ALTER TABLE ULog_tmp RENAME TO ULog;
ALTER TABLE ULogAppendedOffsets_tmp RENAME TO ULogAppendedOffsets;
ALTER TABLE ULogDataset_tmp RENAME TO ULogDataset;
ALTER TABLE ULogField_tmp RENAME TO ULogField;
ALTER TABLE ULogMessageDropout_tmp RENAME TO ULogMessageDropout;
ALTER TABLE ULogMessageFormat_tmp RENAME TO ULogMessageFormat;
ALTER TABLE ULogMessageFormatField_tmp RENAME TO ULogMessageFormatField;
ALTER TABLE ULogMessageLogging_tmp RENAME TO ULogMessageLogging;
ALTER TABLE ULogMessageLoggingTagged_tmp RENAME TO ULogMessageLoggingTagged;
ALTER TABLE ULogMessageInfo_tmp RENAME TO ULogMessageInfo;
ALTER TABLE ULogMessageInfoMultiple_tmp RENAME TO ULogMessageInfoMultiple;
ALTER TABLE ULogMessageInfoMultipleList_tmp RENAME TO ULogMessageInfoMultipleList;
ALTER TABLE ULogMessageInfoMultipleListElement_tmp RENAME TO ULogMessageInfoMultipleListElement;
ALTER TABLE ULogInitialParameter_tmp RENAME TO ULogInitialParameter;
ALTER TABLE ULogChangedParameter_tmp RENAME TO ULogChangedParameter;
ALTER TABLE ULogDefaultParameter_tmp RENAME TO ULogDefaultParameter;

PRAGMA foreign_keys=on;
COMMIT;
