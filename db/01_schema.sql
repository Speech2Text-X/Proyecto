-- Tipos ENUM (coinciden con el DBML acordado)
DO $$ BEGIN
    CREATE TYPE role_enum AS ENUM ('user','admin');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE mode_enum AS ENUM ('batch','stream');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE status_enum AS ENUM ('queued','running','succeeded','failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE artifact_kind_enum AS ENUM ('json','srt','vtt');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE share_kind_enum AS ENUM ('public','private');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE notification_type_enum AS ENUM ('email','whatsapp');
EXCEPTION WHEN duplicate_object THEN null; END $$;
DO $$ BEGIN
    CREATE TYPE notification_status_enum AS ENUM ('pending','sent','failed');
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS users (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email      text NOT NULL UNIQUE,
  name       text,
  pwd_hash   text NOT NULL,
  role       role_enum NOT NULL DEFAULT 'user',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id   uuid NOT NULL,
  name       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
ALTER TABLE projects
  ADD CONSTRAINT fk_projects_owner
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT;

CREATE TABLE IF NOT EXISTS audio_files (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    uuid NOT NULL,
  s3_uri        text NOT NULL,
  duration_sec  int,
  sample_rate   int,
  channels      int,
  format        text,
  size_bytes    bigint,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audio_files_project_id ON audio_files(project_id);
ALTER TABLE audio_files
  ADD CONSTRAINT fk_audio_files_project
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS transcriptions (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audio_id           uuid NOT NULL,
  mode               mode_enum NOT NULL DEFAULT 'batch',
  status             status_enum NOT NULL DEFAULT 'queued',
  language_hint      text,
  language_detected  text,
  model_name         text,
  temperature        numeric,
  beam_size          int,
  confidence         numeric,
  text_full          text,
  artifacts          jsonb,
  started_at         timestamptz,
  finished_at        timestamptz,
  deleted_at         timestamptz
);
CREATE INDEX IF NOT EXISTS idx_transcriptions_audio_id ON transcriptions(audio_id);
CREATE INDEX IF NOT EXISTS idx_transcriptions_status   ON transcriptions(status);
ALTER TABLE transcriptions
  ADD CONSTRAINT fk_transcriptions_audio
  FOREIGN KEY (audio_id) REFERENCES audio_files(id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS segments (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcription_id   uuid NOT NULL,
  start_ms           int  NOT NULL,
  end_ms             int  NOT NULL,
  speaker_label      text,
  text               text NOT NULL,
  confidence         numeric
);
CREATE INDEX IF NOT EXISTS idx_segments_transcription ON segments(transcription_id);
CREATE INDEX IF NOT EXISTS idx_segments_start_ms      ON segments(start_ms);
ALTER TABLE segments
  ADD CONSTRAINT fk_segments_transcription
  FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS transcription_artifacts (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcription_id   uuid NOT NULL,
  kind               artifact_kind_enum NOT NULL,
  s3_uri             text NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE(transcription_id, kind)
);
ALTER TABLE transcription_artifacts
  ADD CONSTRAINT fk_artifacts_transcription
  FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE;

CREATE TABLE IF NOT EXISTS shares (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcription_id   uuid NOT NULL,
  kind               share_kind_enum NOT NULL DEFAULT 'private',
  token              text NOT NULL UNIQUE,
  can_edit           bool NOT NULL DEFAULT false,
  expires_at         timestamptz,
  created_by         uuid,
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_shares_token           ON shares(token);
CREATE INDEX IF NOT EXISTS idx_shares_transcription   ON shares(transcription_id);
ALTER TABLE shares
  ADD CONSTRAINT fk_shares_transcription
  FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE;
ALTER TABLE shares
  ADD CONSTRAINT fk_shares_created_by
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS notifications (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcription_id   uuid NOT NULL,
  user_id            uuid,
  type               notification_type_enum NOT NULL,
  target             text NOT NULL,
  status             notification_status_enum NOT NULL DEFAULT 'pending',
  payload            jsonb,
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notifications_transcription ON notifications(transcription_id);
ALTER TABLE notifications
  ADD CONSTRAINT fk_notifications_transcription
  FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE;
ALTER TABLE notifications
  ADD CONSTRAINT fk_notifications_user
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS notification_subscriptions (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcription_id   uuid NOT NULL,
  user_id            uuid NOT NULL,
  channels           text NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (transcription_id, user_id)
);
ALTER TABLE notification_subscriptions
  ADD CONSTRAINT fk_subs_transcription
  FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE CASCADE;
ALTER TABLE notification_subscriptions
  ADD CONSTRAINT fk_subs_user
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
