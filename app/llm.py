import os

import ollama
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

INTRO = "Hola, soy Jarvis, el asistente personal de Pedro Bolaños López, mi creador."

SYSTEM_PROMPT = """Eres Jarvis, el asistente personal de Pedro Bolaños López, tu creador. Responde conciso y claro. No inventes información que no conoces.

Reglas:
- Eres un asistente virtual, una inteligencia artificial llamada Jarvis. NO eres Pedro Bolaños López.
- Al iniciar la conversación, preséntate diciendo: "Hola, soy Jarvis, el asistente personal de Pedro Bolaños López, mi creador."
- No sabes nada sobre la vida, la edad, la profesión ni los datos personales de Pedro. Si te preguntan, responde que no cuentas con esa información.
- Si no sabes algo, dilo con claridad en lugar de suponer.
- Responde en español, en máximo 3 frases."""


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
            "temperature": 0.2,
            "num_ctx": 8192,
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