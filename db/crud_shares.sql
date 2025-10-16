-- CREATE
INSERT INTO shares (transcription_id, kind, token, can_edit, expires_at, created_by)
VALUES (:transcription_id, COALESCE(:kind,'private'), :token, COALESCE(:can_edit,false), :expires_at, :created_by)
RETURNING id, transcription_id, kind, token, can_edit, expires_at, created_at;

-- READ por token (si no expiró)
SELECT s.id, s.transcription_id, s.kind, s.can_edit, s.expires_at, t.status
FROM shares s
JOIN transcriptions t ON t.id = s.transcription_id
WHERE s.token = :token
  AND (s.expires_at IS NULL OR s.expires_at > NOW());

-- LIMPIEZA expirados
DELETE FROM shares
WHERE expires_at IS NOT NULL AND expires_at <= NOW()
RETURNING id, token;

-- UPDATE
UPDATE shares
SET kind      = COALESCE(:kind, kind),
    can_edit  = COALESCE(:can_edit, can_edit),
    expires_at= COALESCE(:expires_at, expires_at)
WHERE id = :id
RETURNING id, kind, can_edit, expires_at;

-- DELETE
DELETE FROM shares WHERE id = :id RETURNING id;
