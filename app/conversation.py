import asyncio
import os

from app.database.connection import get_pool
from app.llm import OLLAMA_MODEL, generate_response
from app.services.company_cache import get_company_context

MAX_HISTORY_MESSAGES = int(os.getenv("HISTORY_LIMIT", "6"))


async def process_incoming_message(
    platform: str,
    platform_user_id: str,
    display_name: str | None,
    text: str,
    platform_message_id: str | None = None,
) -> str | None:
    """Procesa un mensaje de WhatsApp o Telegram.

    Guarda el mensaje del usuario y la respuesta del asistente.
    Devuelve None si el mensaje ya había sido procesado (reintento).
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Registrar o recuperar al usuario
            user = await conn.fetchrow("""
                INSERT INTO users (platform, platform_user_id, display_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (platform, platform_user_id)
                DO UPDATE SET display_name = COALESCE(
                    EXCLUDED.display_name, users.display_name
                )
                RETURNING id;
            """, platform, platform_user_id, display_name)
            user_id = user["id"]

            # 2. Crear o recuperar su conversación
            conversation = await conn.fetchrow("""
                INSERT INTO conversations (user_id)
                VALUES ($1)
                ON CONFLICT (user_id)
                DO UPDATE SET updated_at = NOW()
                RETURNING id, summary;
            """, user_id)
            conversation_id = conversation["id"]
            summary = conversation["summary"]

            # 3. Guardar el mensaje recibido
            if platform_message_id:
                inserted = await conn.fetchrow("""
                    INSERT INTO messages (
                        conversation_id, role, content, platform_message_id
                    )
                    VALUES ($1, 'user', $2, $3)
                    ON CONFLICT DO NOTHING
                    RETURNING id;
                """, conversation_id, text, platform_message_id)

                # Si ya existía, no procesamos ni respondemos otra vez
                if inserted is None:
                    return None
            else:
                await conn.execute("""
                    INSERT INTO messages (conversation_id, role, content)
                    VALUES ($1, 'user', $2);
                """, conversation_id, text)

            # 4. Recuperar el historial reciente
            rows = await conn.fetch("""
                SELECT role, content
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC, id DESC
                LIMIT $2;
            """, conversation_id, MAX_HISTORY_MESSAGES)

    # La consulta devuelve del más reciente al más antiguo;
    # Ollama necesita el orden cronológico.
    messages = [
        {"role": row["role"], "content": row["content"]}
        for row in reversed(rows)
    ]

    # 5. Contexto empresarial desde la caché (RAM)
    company_context = get_company_context()

    # 6. Generar respuesta sin bloquear el event loop
    respuesta = await asyncio.to_thread(
        generate_response,
        messages,
        OLLAMA_MODEL,
        company_context,
        summary,
    )

    # 7. Guardar la respuesta del asistente
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES ($1, 'assistant', $2);
            """, conversation_id, respuesta)

            await conn.execute("""
                UPDATE conversations SET updated_at = NOW() WHERE id = $1;
            """, conversation_id)

    return respuesta
