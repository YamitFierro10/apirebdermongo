"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from fastapi import Request
from openai import OpenAI
from twilio.rest import Client
from dotenv import load_dotenv
import os
from pruebados.api import handle


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configura las claves de API
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")


# Función para obtener respuesta de OpenAI
def get_ai_response(message):
    response = OpenAI.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente de chat útil."},
            {"role": "user", "content": message}
        ]
    )
    return response['choices'][0]['message']['content']


# Función para manejar mensajes entrantes de Twilio

async def handle_incoming_message(request: Request):
    form = await request.form()  # Extrae el formulario de la solicitud
    incoming_msg = form.get("Body")  # Extrae el mensaje
    from_number = form.get("From")  # Extrae el número de remitente

    # Generar la respuesta AI usando OpenAI
    ai_reply = get_ai_response(incoming_msg)
    client = Client(twilio_sid, twilio_token)
        
    # Enviar la respuesta de vuelta al usuario por WhatsApp
    client.messages.create(
        from_="whatsapp:+14155238886",  # Número de Twilio
        body=ai_reply,
        to="whatsapp:+573102423332"  # Tu número de WhatsApp 
    )
    print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
    # Retornar una respuesta JSON
    return {"status": "success", "response": ai_reply}


# Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])


