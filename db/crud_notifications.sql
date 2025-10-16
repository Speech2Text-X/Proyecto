-- CREATE
INSERT INTO notifications (transcription_id, user_id, type, target, status, payload)
VALUES (:transcription_id, :user_id, :type, :target, COALESCE(:status,'pending'), :payload::jsonb)
RETURNING id, transcription_id, type, target, status, created_at;

-- READ por transcripción
SELECT * FROM notifications
WHERE transcription_id = :transcription_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;

-- UPDATE estado
UPDATE notifications
SET status = :status,
    payload = COALESCE(:payload::jsonb, payload)
WHERE id = :id
RETURNING id, status, payload, created_at;

-- DELETE
DELETE FROM notifications WHERE id = :id RETURNING id;
