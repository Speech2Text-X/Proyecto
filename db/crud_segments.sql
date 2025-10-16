-- CREATE uno
INSERT INTO segments (transcription_id, start_ms, end_ms, speaker_label, text, confidence)
VALUES (:transcription_id, :start_ms, :end_ms, :speaker_label, :text, :confidence)
RETURNING id;

-- READ por transcripción
SELECT id, start_ms, end_ms, speaker_label, text, confidence
FROM segments
WHERE transcription_id = :transcription_id
ORDER BY start_ms ASC
LIMIT :limit OFFSET :offset;

-- UPDATE
UPDATE segments
SET speaker_label = COALESCE(:speaker_label, speaker_label),
    text          = COALESCE(:text, text),
    confidence    = COALESCE(:confidence, confidence)
WHERE id = :id
RETURNING id, speaker_label, text, confidence;

-- DELETE
DELETE FROM segments WHERE id = :id RETURNING id;
DELETE FROM segments WHERE transcription_id = :transcription_id RETURNING id;
