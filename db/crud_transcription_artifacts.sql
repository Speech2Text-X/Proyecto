-- UPSERT por (transcription_id, kind)
INSERT INTO transcription_artifacts (transcription_id, kind, s3_uri)
VALUES (:transcription_id, :kind, :s3_uri)
ON CONFLICT (transcription_id, kind) DO UPDATE
SET s3_uri = EXCLUDED.s3_uri,
    created_at = NOW()
RETURNING id, transcription_id, kind, s3_uri, created_at;

-- READ
SELECT * FROM transcription_artifacts
WHERE transcription_id = :transcription_id
ORDER BY created_at DESC;

-- DELETE
DELETE FROM transcription_artifacts
WHERE transcription_id = :transcription_id AND kind = :kind
RETURNING id;
