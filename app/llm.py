import os

import ollama
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")

SYSTEM_PROMPT = """
Eres el asistente virtual de Biaani, un centro STEM Maker.

Tu función es orientar a los usuarios sobre los servicios,
talleres, actividades y funcionamiento de la academia.

Responde en español, de forma clara, amable y precisa.
Tus respuestas serán leídas en WhatsApp: sé breve (máximo 4 o 5 líneas).

Si no tienes información suficiente para responder,
indica que no cuentas con ese dato. No inventes información.
"""


def generate_response(messages: list, model: str | None = None) -> str:
    """Genera una respuesta con Ollama a partir del historial de mensajes."""
    response = ollama.chat(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
        ],
        think=False,
        options={
            "temperature": 0.2,  # más directo y predecible
            "num_ctx": 4096,
            "num_predict": 200,  # máximo de TOKENS (no palabras) por respuesta
        },
    )
    return response["message"]["content"].strip()
