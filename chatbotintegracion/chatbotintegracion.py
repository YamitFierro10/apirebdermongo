from fastapi import FastAPI, Request
from twilio.rest import Client
from chatbot import get_ai_response
import os
from dotenv import load_dotenv
from chatbotintegracion.api import handle

# Cargar variables de entorno
load_dotenv()

# Configurar API de Twilio
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

app = FastAPI()

@app.post("/whatsapp")
async def handle_incoming_message(request: Request):
    form = await request.form()
    incoming_msg = form.get("Body")  # Mensaje del usuario
    from_number = form.get("From")   # Número del usuario

    # Obtener respuesta del chatbot
    ai_reply = get_ai_response(incoming_msg, from_number)

    # Enviar respuesta por WhatsApp
    client = Client(twilio_sid, twilio_token)
    client.messages.create(
        from_="whatsapp:+14155238886",  # Número de Twilio
        body=ai_reply,
        to=from_number
    )

    print(f"Mensaje enviado a {from_number}: {ai_reply}")
    return {"status": "success", "response": ai_reply}

app.include_router(handle)