import os

import ollama
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_MODEL = DEFAULT_MODEL

INTRO = "Hola, soy Jarvis, el asistente personal de Pedro Bolaños López, mi creador."

SYSTEM_PROMPT = """Eres Jarvis, el asistente personal de Pedro Bolaños López, tu creador. Responde en español, conciso y claro, en máximo 3 frases. No inventes información que no conoces.

Si el usuario te saluda, salúdalo y pregunta en qué puedes ayudarle.
Si te preguntan por Pedro, di que es tu creador y que no tienes más datos sobre él.
Nunca le pidas al usuario información personal."""


def generate_response(
    messages: list,
    model: str | None = None,
    company_context: dict | None = None,
    summary: str = "",
) -> str:
    """Genera una respuesta con Ollama.

    - messages: historial reciente (orden cronológico)
    - company_context: información oficial cargada desde PostgreSQL (caché)
    - summary: memoria resumida de la conversación (opcional)
    """
    context_text = ""
    if company_context:
        context_text = (
            "\n\nINFORMACIÓN OFICIAL (datos sobre ti y tu creador; además puedes "
            "usar lo que el usuario te haya dicho en esta conversación):\n"
        )
        for key, item in company_context.items():
            context_text += f"\n{key}: {item['content']}"

    if summary:
        context_text += f"\n\nRESUMEN DE LA CONVERSACIÓN ANTERIOR:\n{summary}"

    response = ollama.chat(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + context_text},
            *messages,
        ],
        think=False,
        options={
            "temperature": 0.2,
            "num_ctx": 4096,
            "num_predict": 300,
        },
    )
    answer = response["message"]["content"].strip()

    # Primera respuesta de la conversación: siempre empieza con la presentación,
    # sin repetirla si el modelo ya se presentó como Jarvis.
    is_first_reply = len(messages) == 1
    if is_first_reply and "jarvis" not in answer[:80].lower():
        answer = f"{INTRO} {answer}"

    return answer
