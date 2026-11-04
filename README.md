# Chatbot de WhatsApp para Biaani

WhatsApp Cloud API → ngrok → FastAPI → Ollama → respuesta por WhatsApp. Historial en PostgreSQL.

## Estructura

```
app/
  api.py        Servidor FastAPI: verificación del webhook y recepción de mensajes
  llm.py        Llamada a Ollama (system prompt, temperatura, límite de tokens)
  whatsapp.py   Envío de respuestas con la Cloud API
  db.py         Historial en PostgreSQL (o memoria si no hay DATABASE_URL)
  main.py       Chat de prueba en terminal: python -m app.main --model llama3.2:1b
```

## Puesta en marcha

1. Copia estos archivos dentro de tu carpeta `whatsapp-chatbot` (sobrescribe `app/`).
2. `source .venv/bin/activate` (Windows: `.venv\Scripts\Activate.ps1`) y `pip install -r requirements.txt`
3. Copia `.env.example` a `.env` y llena `META_VERIFY_TOKEN`, `WHATSAPP_TOKEN` y `PHONE_NUMBER_ID`.
4. Prueba el modelo: `python -m app.main`
5. Terminal 1: `uvicorn app.api:app --reload --host 0.0.0.0 --port 8000`
6. Terminal 2: `ngrok http 8000 --url https://flaky-stout-cheesy.ngrok-free.dev`
7. En Meta: URL de devolución `https://flaky-stout-cheesy.ngrok-free.dev/webhook`, mismo verify token, y suscribe el campo `messages`.
8. Escribe desde tu celular al número de prueba y espera la respuesta.

## PostgreSQL (opcional al inicio)

Crea la base `biaani_chatbot` (ver `schema.sql`) y agrega a `.env`:

```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/biaani_chatbot
```

## Notas

- El token de acceso de Meta de prueba dura 24 h. Si el bot deja de responder y ves error 401/190 en la terminal de uvicorn, genera uno nuevo y actualiza `.env`.
- Los números mexicanos llegan como `521...` pero la lista de prueba usa `52...`; `whatsapp.py` lo normaliza.
- `num_predict` en Ollama son **tokens**, no palabras.
- Opcional: define `META_APP_SECRET` para validar que los POST realmente vienen de Meta.
