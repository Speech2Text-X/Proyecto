-- Usuarios
INSERT INTO users (email, name, pwd_hash) VALUES
('demo@stx.app','Demo','hash-demo') ON CONFLICT DO NOTHING;

-- Proyecto
WITH u AS (SELECT id FROM users WHERE email='demo@stx.app')
INSERT INTO projects (owner_id, name)
SELECT id, 'Entrevistas 2025' FROM u;

-- Audio de muestra
WITH p AS (SELECT id FROM projects ORDER BY created_at DESC LIMIT 1)
INSERT INTO audio_files (project_id, s3_uri, duration_sec, sample_rate, channels, format, size_bytes)
SELECT id, 's3://bucket-demo/intro.mp3', 12, 44100, 2, 'mp3', 123456 FROM p;

-- Transcripción placeholder
WITH a AS (SELECT id FROM audio_files ORDER BY created_at DESC LIMIT 1)
INSERT INTO transcriptions (audio_id, status, mode, model_name, started_at, finished_at, text_full)
SELECT id, 'succeeded', 'batch', 'faster-whisper-small', NOW()-INTERVAL '1 min', NOW(),
'Hola, esta es una transcripción de prueba.' FROM a;
