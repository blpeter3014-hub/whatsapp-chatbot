-- Ejecutar una vez en pgAdmin (Query Tool) o con psql.
-- La app también crea la tabla automáticamente al iniciar.
CREATE DATABASE biaani_chatbot;

-- Conéctate a biaani_chatbot y luego:
CREATE TABLE IF NOT EXISTS messages (
    id            BIGSERIAL PRIMARY KEY,
    wa_message_id TEXT UNIQUE,
    wa_id         TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_wa_id_created
    ON messages (wa_id, created_at DESC);
