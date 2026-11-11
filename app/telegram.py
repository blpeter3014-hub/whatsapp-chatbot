import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_message(chat_id: int | str, text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[telegram] Falta TELEGRAM_BOT_TOKEN en .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": text[:4096]},
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[telegram] Error de red: {e}")
        return False

    if r.status_code >= 400:
        print(f"[telegram] Error {r.status_code}: {r.text}")
        return False
    return True