import os
import time
from datetime import datetime

from twilio.rest import Client

from chatbotintegracion.chatbot import get_ai_response
from chatbotintegracion.database import get_collection


# =========================
# 🔹 CONFIG TWILIO
# =========================
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(twilio_sid, twilio_token) if twilio_sid and twilio_token else None


# =========================
# 🚀 ENVIAR WHATSAPP CON RETRY
# =========================
def enviar_whatsapp_con_retry(numero, mensaje):
    if not twilio_client:
        print("⚠️ Twilio no configurado")
        return

    for intento in range(3):
        try:
            twilio_client.messages.create(
                body=mensaje,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=numero
            )
            print("📤 Mensaje enviado correctamente")
            return

        except Exception as e:
            print(f"❌ Twilio intento {intento + 1}:", e)
            time.sleep(2)

    print("🚨 No se pudo enviar el mensaje después de varios intentos")


# =========================
# 🧠 GENERAR RESPUESTA SEGURA (IA)
# =========================
def generar_respuesta_segura(mensaje, numero):
    for intento in range(3):
        try:
            respuesta = get_ai_response(mensaje, numero)

            if respuesta:
                return respuesta

        except Exception as e:
            print(f"❌ IA intento {intento + 1}:", e)
            time.sleep(2)

    return "Lo siento, estoy teniendo dificultades técnicas. Intenta nuevamente 🙏"


# =========================
# 🔥 PROCESAMIENTO COMPLETO
# =========================
def procesar_mensaje_pro(mensaje, numero):
    print("🔥 Iniciando procesamiento PRO")

    col = get_collection()

    # =========================
    # 👤 GUARDAR MENSAJE USUARIO
    # =========================
    if col is not None:
        try:
            col.insert_one({
                "usuario": numero,
                "mensaje": mensaje,
                "tipo": "usuario",
                "timestamp": datetime.utcnow()
            })
            print("💾 Usuario guardado")
        except Exception as e:
            print("❌ Error guardando usuario:", e)

    # =========================
    # 🤖 GENERAR RESPUESTA IA
    # =========================
    respuesta = generar_respuesta_segura(mensaje, numero)

    print("🤖 Respuesta IA:", respuesta)

    # =========================
    # 🤖 GUARDAR RESPUESTA BOT
    # =========================
    if col is not None:
        try:
            col.insert_one({
                "usuario": numero,
                "mensaje": respuesta,
                "tipo": "bot",
                "timestamp": datetime.utcnow()
            })
            print("💾 Bot guardado")
        except Exception as e:
            print("❌ Error guardando bot:", e)

    # =========================
    # 📤 ENVIAR RESPUESTA WHATSAPP
    # =========================
    enviar_whatsapp_con_retry(numero, respuesta)