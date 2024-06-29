BEGIN;
PRAGMA foreign_keys=off;

-- Change REAL timestamps to INT. SQLITE only supports INT64, but ULog -- changed from REAL
-- timestamps are UINT64. We accept losing 1 bit at the top end, since 2^63
-- microseconds = 400,000 years. which should be enough.

ALTER TABLE ULog RENAME COLUMN StartTimestamp TO StartTimestamp_old;
ALTER TABLE ULog ADD COLUMN StartTimestamp INT;
UPDATE ULog SET StartTimestamp = CAST(StartTimestamp_old AS INT);

ALTER TABLE ULog RENAME COLUMN LastTimestamp TO LastTimestamp_old;
ALTER TABLE ULog ADD COLUMN LastTimestamp INT;
UPDATE ULog SET LastTimestamp = CAST(LastTimestamp_old AS INT);

ALTER TABLE ULogMessageDropout RENAME COLUMN Timestamp TO Timestamp_old;
ALTER TABLE ULogMessageDropout ADD COLUMN Timestamp INT;
UPDATE ULogMessageDropout SET Timestamp = CAST(Timestamp_old AS INT);

ALTER TABLE ULogMessageDropout RENAME COLUMN Duration TO Duration_old;
ALTER TABLE ULogMessageDropout ADD COLUMN Duration INT;
UPDATE ULogMessageDropout SET Duration = CAST(Duration_old AS INT);

ALTER TABLE ULogMessageLogging RENAME COLUMN Timestamp TO Timestamp_old;
ALTER TABLE ULogMessageLogging ADD COLUMN Timestamp INT;
UPDATE ULogMessageLogging SET Timestamp = CAST(Timestamp_old AS INT);

ALTER TABLE ULogMessageLoggingTagged RENAME COLUMN Timestamp TO Timestamp_old;
ALTER TABLE ULogMessageLoggingTagged ADD COLUMN Timestamp INT;
UPDATE ULogMessageLoggingTagged SET Timestamp = CAST(Timestamp_old AS INT);

ALTER TABLE ULogChangedParameter RENAME COLUMN Timestamp TO Timestamp_old;
ALTER TABLE ULogChangedParameter ADD COLUMN Timestamp INT;
UPDATE ULogChangedParameter SET Timestamp = CAST(Timestamp_old AS INT);

PRAGMA foreign_keys=on;
COMMIT;
