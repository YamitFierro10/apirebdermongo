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
from dotenv import load_dotenv
from chatbotintegracion.chatbot import get_ai_response
from chatbotintegracion.api import handle
from chatbotintegracion import chatbot as chatbot_module
from google import genai
import os

# ===========================================================
# CARGAR VARIABLES DE ENTORNO
# ===========================================================
load_dotenv()

# ===========================================================
# CONFIGURAR FASTAPI
# ===========================================================
app = FastAPI()

# ===========================================================
# STARTUP: INICIALIZAR GEMINI UNA SOLA VEZ
# ===========================================================
@app.on_event("startup")
def startup_event():
    """
    Inicializa el cliente Gemini SOLO una vez al arrancar FastAPI.
    Evita el error del SDK: '_async_httpx_client'
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("❌ ERROR: GEMINI_API_KEY no está configurada.")
        chatbot_module.client = None
        return

    try:
        chatbot_module.client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini inicializado correctamente.")
    except Exception as e:
        print(f"❌ ERROR al inicializar Gemini: {e}")
        chatbot_module.client = None

# ===========================================================
# ENDPOINT PRINCIPAL PARA WHATSAPP (TWILIO)
# ===========================================================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    # Twilio envía los datos en form-data
    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    # Si envían vacío, respondemos vacío (Twilio requiere TwiML)
    if not incoming_msg:
        return MessagingResponse()

    # Procesar mensaje con Gemini
    ai_reply = get_ai_response(incoming_msg, from_number)

    # Crear respuesta TwiML
    resp = MessagingResponse()
    resp.message(ai_reply)

    # Logs
    print(f"📩 Recibido de {from_number}: {incoming_msg}")
    print(f"🤖 Enviado: {ai_reply}")

    return resp

# ===========================================================
# ENDPOINT SECUNDARIO /handle (POST + GET)
# ===========================================================
app.add_api_route("/handle", handle, methods=["GET", "POST"])


