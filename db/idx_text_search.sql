-- Índice trigram para búsqueda rápida en text_full
CREATE INDEX IF NOT EXISTS idx_transcriptions_text_trgm
  ON transcriptions USING gin (text_full gin_trgm_ops);
