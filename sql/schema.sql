-- Usuarios de WhatsApp y Telegram
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    platform_user_id VARCHAR(150) NOT NULL,
    display_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (platform, platform_user_id)
);

-- Una conversación por usuario y plataforma
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE
        REFERENCES users(id) ON DELETE CASCADE,
    summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Historial de mensajes
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL
        REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL
        CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    platform_message_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Por si la tabla ya existía sin esta columna (versión del PDF)
ALTER TABLE messages ADD COLUMN IF NOT EXISTS platform_message_id TEXT;

CREATE INDEX IF NOT EXISTS idx_messages_conversation_date
ON messages (conversation_id, created_at DESC);

-- Evita procesar dos veces el mismo mensaje (Meta y Telegram reintentan)
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_platform_message
ON messages (platform_message_id)
WHERE platform_message_id IS NOT NULL;

-- Información estática del asistente
CREATE TABLE IF NOT EXISTS company_knowledge (
    id BIGSERIAL PRIMARY KEY,
    knowledge_key VARCHAR(150) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
