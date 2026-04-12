import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from google import genai

# 🔥 importar chatbot (para inyectar cliente)
import chatbotintegracion.chatbot as chatbot_module

# 🔥 importar servicios
from chatbotintegracion.services.whatsapp import (
    procesar_mensaje_pro,
    mensaje_seguimiento
)

load_dotenv()


# =========================
# 🔹 LIFESPAN (INICIALIZAR GEMINI)
# =========================
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


# =========================
# 🚀 APP
# =========================
app = FastAPI(title="Chatbot Integración", lifespan=lifespan)


# =========================
# 📩 WEBHOOK WHATSAPP
# =========================
@app.post("/whatsapp")
async def handle_incoming_message(request: Request, background_tasks: BackgroundTasks):

    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("No recibí mensaje 🤔")
        return Response(content=str(resp), media_type="application/xml")

    # 🔥 Procesamiento principal (IA + Mongo + envío)
    background_tasks.add_task(procesar_mensaje_pro, incoming_msg, from_number)

    # ⏱️ Seguimiento automático (5 minutos)
    background_tasks.add_task(mensaje_seguimiento, from_number, 300)

    return Response(content=str(resp), media_type="application/xml")


# =========================
# 🩺 HEALTH CHECK
# =========================
@app.get("/")
def root():
    return {"status": "ok"}