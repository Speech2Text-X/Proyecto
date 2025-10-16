-- CREATE
INSERT INTO audio_files (project_id, s3_uri, duration_sec, sample_rate, channels, format, size_bytes)
VALUES (:project_id, :s3_uri, :duration_sec, :sample_rate, :channels, :format, :size_bytes)
RETURNING id, project_id, s3_uri, duration_sec, sample_rate, channels, format, size_bytes, created_at;

-- READ
SELECT * FROM audio_files WHERE id = :id;
SELECT * FROM audio_files
WHERE project_id = :project_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;

-- UPDATE
UPDATE audio_files
SET duration_sec = COALESCE(:duration_sec, duration_sec),
    sample_rate  = COALESCE(:sample_rate,  sample_rate),
    channels     = COALESCE(:channels,     channels),
    format       = COALESCE(:format,       format)
WHERE id = :id
RETURNING *;

-- DELETE
DELETE FROM audio_files WHERE id = :id RETURNING id;
