-- UPSERT único por (transcription_id, user_id)
INSERT INTO notification_subscriptions (transcription_id, user_id, channels)
VALUES (:transcription_id, :user_id, :channels)
ON CONFLICT (transcription_id, user_id) DO UPDATE
SET channels = EXCLUDED.channels,
    created_at = NOW()
RETURNING id, transcription_id, user_id, channels, created_at;

-- READ
SELECT * FROM notification_subscriptions
WHERE transcription_id = :transcription_id;

-- DELETE
DELETE FROM notification_subscriptions
WHERE transcription_id = :transcription_id AND user_id = :user_id
RETURNING id;
