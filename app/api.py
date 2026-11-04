import hashlib
import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app import db
from app.llm import generate_response
from app.whatsapp import send_text

load_dotenv()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
APP_SECRET = os.getenv("META_APP_SECRET")  # opcional: valida la firma de Meta
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Biaani Chatbot API",
    description="Webhook y API del chatbot Biaani",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"status": "online", "application": "Biaani Chatbot"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verificación incorrecta")


def _valid_signature(body: bytes, header: str | None) -> bool:
    if not APP_SECRET:
        return True  # validación desactivada
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def process_message(wa_id: str, wa_message_id: str, text: str) -> None:
    """Se ejecuta en segundo plano: así respondemos 200 a Meta de inmediato."""
    try:
        db.save_message(wa_id, "user", text, wa_message_id)
        history = db.get_history(wa_id, HISTORY_LIMIT)
        answer = generate_response(history)
        if not answer:
            answer = "Lo siento, no pude generar una respuesta. ¿Puedes repetir tu pregunta?"
        if send_text(wa_id, answer):
            db.save_message(wa_id, "assistant", answer)
    except Exception as e:  # noqa: BLE001
        print(f"[process_message] Error: {e!r}")


@app.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not _valid_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Firma inválida")

    data = await request.json()

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            # Los "statuses" (entregado/leído) también llegan aquí: se ignoran.
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    wa_id = msg.get("from")
                    if wa_id and not db.already_processed(msg["id"]):
                        background.add_task(
                            send_text,
                            wa_id,
                            "Por ahora solo puedo leer mensajes de texto. 🙂",
                        )
                    continue

                wa_id = msg["from"]
                wa_message_id = msg["id"]
                text = msg["text"]["body"]

                if db.already_processed(wa_message_id):
                    continue

                print(f"[webhook] {wa_id}: {text}")
                background.add_task(process_message, wa_id, wa_message_id, text)

    return {"status": "received"}
