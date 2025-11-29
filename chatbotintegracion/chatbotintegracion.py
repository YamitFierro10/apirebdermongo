# from fastapi import FastAPI, Request
# from twilio.rest import Client
# from chatbotintegracion.chatbot import get_ai_response
# import os
# from dotenv import load_dotenv
# from chatbotintegracion.api import handle

# # Cargar variables de entorno
# load_dotenv()

# # Configurar API de Twilio
# twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
# twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# app = FastAPI()

# @app.post("/whatsapp")
# async def handle_incoming_message(request: Request):
#     form = await request.form()
#     incoming_msg = form.get("Body")  # Mensaje del usuario
#     from_number = form.get("From")   # Número del usuario

#     # Obtener respuesta del chatbot
#     ai_reply = get_ai_response(incoming_msg, from_number)

#     # Enviar respuesta por WhatsApp
#     client = Client(twilio_sid, twilio_token)
#     client.messages.create(
#         from_="whatsapp:+14155238886",  # Número de Twilio
#         body=ai_reply,
#         to=from_number
#     )

#     print(f"Mensaje enviado a {from_number}: {ai_reply}")
#     return {"status": "success", "response": ai_reply}



# app.add_api_route("/handle", handle, methods=["POST"])

from fastapi import FastAPI, Request
from twilio.twiml.messaging_response import MessagingResponse

from chatbotintegracion.chatbot import get_ai_response
from chatbotintegracion.api import handle
from chatbotintegracion import chatbot as chatbot_module

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI()


# ===========================
# INICIALIZAR GEMINI SOLO 1 VEZ
# ===========================
@app.on_event("startup")
def startup_event():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurada.")
        chatbot_module.client = None
        return

    try:
        chatbot_module.client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini inicializado correctamente.")
    except Exception as e:
        print(f"❌ Error inicializando Gemini: {e}")
        chatbot_module.client = None


# ===========================
# ENDPOINT WHATSAPP
# ===========================
@app.post("/whatsapp")
async def whatsapp_endpoint(request: Request):

    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    if not incoming_msg:
        return MessagingResponse()

    ai_reply = get_ai_response(incoming_msg, from_number)

    resp = MessagingResponse()
    resp.message(ai_reply)

    print(f"📩 Recibido de {from_number}: {incoming_msg}")
    print(f"🤖 Enviado: {ai_reply}")

    return resp


# ===========================
# ENDPOINT /handle
# ===========================
app.add_api_route("/handle", handle, methods=["GET", "POST"])



