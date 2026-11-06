import os

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")


def normalize_recipient(wa_id: str) -> str:
    """Los números de México llegan como 521XXXXXXXXXX pero la lista de
    destinatarios de prueba de Meta usa 52XXXXXXXXXX. Quitamos el '1'."""
    if wa_id.startswith("521") and len(wa_id) == 13:
        return "52" + wa_id[3:]
    return wa_id


def send_text(to: str, body: str) -> bool:
    token = os.getenv("META_ACCESS_TOKEN") or os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID") or os.getenv("PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        print("[whatsapp] Faltan META_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID en .env")
        return False

    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": normalize_recipient(to),
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }
    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[whatsapp] Error de red: {e}")
        return False

    if r.status_code >= 400:
        # 401/190 normalmente = token vencido
        print(f"[whatsapp] Error {r.status_code}: {r.text}")
        return False
    return True
