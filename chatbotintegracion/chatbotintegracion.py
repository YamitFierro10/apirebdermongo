# chatbotintegracion/chatbotintegracion.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from google import genai

from chatbotintegracion.chatbot import get_ai_response
from chatbotintegracion import chatbot as chatbot_module
from chatbotintegracion.database import collection
from datetime import datetime

load_dotenv()

# 🔹 Twilio config
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(twilio_sid, twilio_token) if twilio_sid and twilio_token else None

# 🔹 Lifespan (reemplaza on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurada.")
        chatbot_module.client = None
    else:
        try:
            chatbot_module.client = genai.Client(api_key=GEMINI_API_KEY)
            print("✅ Cliente Gemini inicializado.")
        except Exception as e:
            print(f"❌ ERROR al iniciar Gemini: {e}")
            chatbot_module.client = None

    yield

    print("🔒 Cerrando aplicación...")

app = FastAPI(title="Chatbot Integración", lifespan=lifespan)

def procesar_mensaje(mensaje, numero):
    try:
        print("🔥 Procesando mensaje")

        print("📦 Collection:", collection)

        # 🔴 PRUEBA DIRECTA A MONGO
        test = collection.insert_one({
            "test": "conexion",
        })

        print("✅ Insert test:", test.inserted_id)

        # IA
        ai_reply = get_ai_response(mensaje, numero)

        # guardar usuario
        collection.insert_one({
            "usuario": numero,
            "mensaje": mensaje,
            "tipo": "usuario"
        })

        # guardar bot
        collection.insert_one({
            "usuario": numero,
            "mensaje": ai_reply,
            "tipo": "bot"
        })

        # enviar mensaje
        twilio_client.messages.create(
            body=ai_reply,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=numero
        )

    except Exception as e:
        print("❌ ERROR MONGO:", e)

        
# 🔹 Webhook WhatsApp
@app.post("/whatsapp")
async def handle_incoming_message(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("No recibí mensaje 🤔")
        return Response(content=str(resp), media_type="application/xml")

    # 🔥 enviar a procesamiento en segundo plano
    background_tasks.add_task(procesar_mensaje, incoming_msg, from_number)

    # 🔥 respuesta rápida a Twilio
    resp.message("Estoy procesando tu mensaje... ⏳")

    return Response(content=str(resp), media_type="application/xml")

@app.get("/")
def root():
    return {"status": "ok"}