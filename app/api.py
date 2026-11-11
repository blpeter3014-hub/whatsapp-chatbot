import asyncio
import hashlib
import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.conversation import process_incoming_message
from app.database.connection import close_db, connect_db
from app.database.initialize import initialize_database
from app.services.company_cache import load_company_cache
from app.telegram import send_message as tg_send
from app.whatsapp import send_text

load_dotenv()

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
APP_SECRET = os.getenv("META_APP_SECRET")  # opcional: valida la firma de Meta
TELEGRAM_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")  # opcional pero recomendado

ERROR_REPLY = "Tuve un problema al generar la respuesta. Intenta de nuevo."


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    await initialize_database()
    await load_company_cache()
    try:
        yield
    finally:
        await close_db()


app = FastAPI(
    title="Chatbot API",
    description="Webhooks de WhatsApp y Telegram con PostgreSQL",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"status": "online", "application": "Jarvis Chatbot"}


# ---------------------------------------------------------------- WhatsApp
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


async def handle_whatsapp(wa_id: str, name: str | None, msg_id: str, text: str):
    try:
        respuesta = await process_incoming_message(
            platform="whatsapp",
            platform_user_id=wa_id,
            display_name=name,
            text=text,
            platform_message_id=msg_id,
        )
        if respuesta:
            await asyncio.to_thread(send_text, wa_id, respuesta)
    except Exception as e:  # noqa: BLE001
        print(f"[whatsapp] Error: {e!r}")
        await asyncio.to_thread(send_text, wa_id, ERROR_REPLY)


@app.post("/webhook")
async def receive_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not _valid_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Firma inválida")

    data = await request.json()

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            names = {
                c.get("wa_id"): c.get("profile", {}).get("name")
                for c in value.get("contacts", [])
            }
            # Los "statuses" (entregado/leído) también llegan aquí: se ignoran.
            for msg in value.get("messages", []):
                wa_id = msg.get("from")
                if msg.get("type") != "text":
                    if wa_id:
                        background.add_task(
                            asyncio.to_thread,
                            send_text,
                            wa_id,
                            "Por ahora solo puedo leer mensajes de texto. 🙂",
                        )
                    continue

                print(f"[whatsapp] {wa_id}: {msg['text']['body']}")
                background.add_task(
                    handle_whatsapp,
                    wa_id,
                    names.get(wa_id),
                    msg["id"],
                    msg["text"]["body"],
                )

    return {"status": "received"}


# ---------------------------------------------------------------- Telegram
async def handle_telegram(
    chat_id: int, name: str | None, message_key: str, text: str
):
    try:
        respuesta = await process_incoming_message(
            platform="telegram",
            platform_user_id=str(chat_id),
            display_name=name,
            text=text,
            platform_message_id=message_key,
        )
        if respuesta:
            await asyncio.to_thread(tg_send, chat_id, respuesta)
    except Exception as e:  # noqa: BLE001
        print(f"[telegram] Error: {e!r}")
        await asyncio.to_thread(tg_send, chat_id, ERROR_REPLY)


@app.post("/telegram")
async def receive_telegram(request: Request, background: BackgroundTasks):
    # Telegram devuelve el secreto que definimos en setWebhook
    if TELEGRAM_SECRET and (
        request.headers.get("X-Telegram-Bot-Api-Secret-Token") != TELEGRAM_SECRET
    ):
        raise HTTPException(status_code=403, detail="Secreto inválido")

    data = await request.json()
    msg = data.get("message")
    if not msg:
        return {"status": "ignored"}

    chat_id = msg["chat"]["id"]
    sender = msg.get("from", {})
    name = sender.get("first_name") or sender.get("username")
    message_key = f"tg-{data.get('update_id')}"

    text = msg.get("text")
    if not text:
        background.add_task(
            asyncio.to_thread,
            tg_send,
            chat_id,
            "Por ahora solo puedo leer mensajes de texto. 🙂",
        )
        return {"status": "received"}

    if text.strip() == "/start":
        text = "Hola"

    print(f"[telegram] {chat_id}: {text}")
    background.add_task(handle_telegram, chat_id, name, message_key, text)
    return {"status": "received"}
