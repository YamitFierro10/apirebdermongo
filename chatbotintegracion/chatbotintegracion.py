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

# chatbotintegracion/chatbotintegracion.py

from fastapi import FastAPI, Request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from chatbotintegracion.chatbot import get_ai_response
from chatbotintegracion import chatbot as chatbot_module
from chatbotintegracion.api import handle  # tu handler existente
from fastapi.responses import Response


import os
from dotenv import load_dotenv
from google import genai

# cargar .env (solo local; en producción usa variables de entorno del servicio)
load_dotenv()

# Twilio
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

if not twilio_sid or not twilio_token:
    print("⚠️ ADVERTENCIA: Twilio no está configurado. WhatsApp no funcionará.")
    twilio_client = None
else:
    twilio_client = Client(twilio_sid, twilio_token)

app = FastAPI(title="Chatbot Integración")

# startup: (opcional) inicializar cliente genai global si prefieres
# aquí lo dejamos opcional; chatbot.get_ai_response crea cliente por request
@app.on_event("startup")
def startup_event():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurada.")
        chatbot_module.client = None
    else:
        try:
            # puedes inicializar global si quieres usar una única instancia:
            chatbot_module.client = genai.Client(api_key=GEMINI_API_KEY)
            print("✅ Cliente Gemini inicializado.")
        except Exception as e:
            print(f"❌ ERROR al iniciar Gemini: {e}")
            chatbot_module.client = None

# @app.post("/whatsapp")
# async def handle_incoming_message(request: Request):
#     form = await request.form()
#     incoming_msg = form.get("Body")
#     from_number = form.get("From")

#     if not incoming_msg:
#         return MessagingResponse()

#     ai_reply = get_ai_response(incoming_msg, from_number)

#     resp = MessagingResponse()
#     resp.message(ai_reply)

#     print(f"📩 Recibido de {from_number}: {incoming_msg}")
#     print(f"🤖 Enviado: {ai_reply}")

#     return Response(content=str(resp), media_type="application/xml")


@app.post("/whatsapp")
async def handle_incoming_message(request: Request):

    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    if not incoming_msg:
        return MessagingResponse()  # Twilio exige respuesta válida

    # === 1. Generar respuesta con Gemini ===
    ai_reply = get_ai_response(incoming_msg, from_number)

    # === 2. Mostrar en consola ===
    print(f"📩 Recibido de {from_number}: {incoming_msg}")
    print(f"🤖 Enviado: {ai_reply}")

    # === 3. Enviar mensaje REAL por WhatsApp ===
    if twilio_client:
        try:
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number,
                body=ai_reply
            )
            print("✅ Mensaje enviado a WhatsApp correctamente")
        except Exception as e:
            print(f"❌ Error enviando WhatsApp con Twilio: {e}")
    else:
        print("⚠️ Twilio no está configurado. No se enviará WhatsApp.")

    # === 4. Enviar respuesta vacía a Twilio ===
    # (TwiML vacío para evitar errores en el webhook)
    resp = MessagingResponse()
    return resp



# mantener /handle (GET y POST)
app.add_api_route("/handle", handle, methods=["GET", "POST"])

# health check simple (evita 404 al entrar en /)
@app.get("/")
def root():
    return {"status": "ok"}




