-- CREATE
INSERT INTO transcriptions (
  audio_id, mode, status, language_hint, model_name, temperature, beam_size, started_at
) VALUES (
  :audio_id, COALESCE(:mode, 'batch'), 'queued',
  :language_hint, :model_name, :temperature, :beam_size, NOW()
)
RETURNING id, audio_id, mode, status, started_at;

-- READ
SELECT * FROM transcriptions WHERE id = :id;

SELECT id, audio_id, mode, status, language_detected, model_name, started_at, finished_at
FROM transcriptions
WHERE audio_id = :audio_id
ORDER BY started_at DESC
LIMIT :limit OFFSET :offset;

-- SEARCH (requiere idx trigram opcional)
SELECT id, audio_id, status
FROM transcriptions
WHERE text_full ILIKE '%' || :q_like || '%'
   OR SIMILARITY(text_full, :q_sim) > 0.2
ORDER BY id DESC
LIMIT :limit OFFSET :offset;

-- UPDATE estados/resultados
UPDATE transcriptions
SET status = 'running'
WHERE id = :id AND status = 'queued'
RETURNING id, status;

UPDATE transcriptions
SET status = 'succeeded',
    language_detected = :language_detected,
    confidence = :confidence,
    text_full = :text_full,
    artifacts = :artifacts::jsonb,
    finished_at = NOW()
WHERE id = :id
RETURNING id, status, language_detected, finished_at;

UPDATE transcriptions
SET status = 'failed', finished_at = NOW()
WHERE id = :id
RETURNING id, status, finished_at;

-- soft delete
UPDATE transcriptions
SET deleted_at = NOW()
WHERE id = :id
RETURNING id, deleted_at;

-- DELETE duro
DELETE FROM transcriptions WHERE id = :id RETURNING id;
