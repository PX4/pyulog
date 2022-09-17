BEGIN;
CREATE TABLE IF NOT EXISTS ULog (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        FileVersion INT,
        StartTimestamp REAL,
        LastTimestamp REAL,
        CompatFlags TEXT,
        IncompatFlags TEXT,
        SyncCount INT,
        HasSync BOOLEAN
);

CREATE TABLE IF NOT EXISTS ULogAppendedOffsets (
        SeriesIndex INTEGER,
        Offset INTEGER,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogDataset (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        DatasetName TEXT,
        MultiId INT,
        MessageId INT,
        TimestampIndex INT,
        ULogId INT REFERENCES ULog (Id),
        UNIQUE (ULogId, DatasetName, MultiId)
);

CREATE TABLE IF NOT EXISTS ULogField (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        TopicName TEXT,
        DataType TEXT,
        ValueArray BLOB,

        DatasetId INTEGER REFERENCES ULogDataset (Id)
);
CREATE INDEX IF NOT EXISTS btree_ulogfield_datasetid ON ULogField(DatasetId);

CREATE TABLE IF NOT EXISTS ULogMessageDropout (
        Timestamp REAL,
        Duration FLOAT,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageFormat (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageFormatField (
        FieldType TEXT,
        ArraySize INT,
        Name TEXT,
        MessageId INT REFERENCES ULogMessageFormat (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageLogging (
        LogLevel INT,
        Timestamp REAL,
        Message TEXT,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageLoggingTagged (
        LogLevel INT,
        Timestamp REAL,
        Tag INT,
        Message TEXT,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageInfo (
        Key TEXT,
        Typename TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogMessageInfoMultiple (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Key TEXT,
        Typename TEXT,
        ULogId INT REFERENCES ULog (Id)
);
CREATE TABLE IF NOT EXISTS ULogMessageInfoMultipleList (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SeriesIndex INTEGER,
        MessageId TEXT REFERENCES ULogMessageInfoMultiple (Id)
);
CREATE TABLE IF NOT EXISTS ULogMessageInfoMultipleListElement (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        SeriesIndex INTEGER,
        Value TEXT,
        ListId TEXT REFERENCES ULogMessageInfoMultipleList (Id)
);

CREATE TABLE IF NOT EXISTS ULogInitialParameter (
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogChangedParameter (
        Timestamp REAL,
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id)
);

CREATE TABLE IF NOT EXISTS ULogDefaultParameter (
        DefaultType INT,
        Key TEXT,
        Value BLOB,
        ULogId INT REFERENCES ULog (Id)
);
COMMIT;
