"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from fastapi import Request
import openai
from twilio.rest import Client
from dotenv import load_dotenv
import os
from pruebados.api import handle


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configura las claves de API
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")


# Función para obtener respuesta de OpenAI
def get_ai_response(message):
    response = openai.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente de chat útil."},
            {"role": "user", "content": message}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

# Función para enviar un mensaje de WhatsApp
# def send_whatsapp_message(message):
#     client.messages.create(
#         from_="whatsapp:+14155238886",  # Cambia esto por tu número de Twilio para WhatsApp
#         body=message,
#         to="whatsapp:+573102423332"
#     )

# Función para manejar mensajes entrantes de Twilio
async def handle_incoming_message(request: Request):
    
    incoming_msg = request.form["Body"]  # Extrae el de la solicitud
    from_number = request.form["From"]
  
        # Generar la respuesta AI usando OpenAI
    ai_reply = get_ai_response(incoming_msg)
    client = Client(twilio_sid, twilio_token)
        
        # Enviar la respuesta de vuelta al usuario por WhatsApp
    client.messages.create(
            from_="whatsapp:+14155238886",  # Número de Twilio
            to="whatsapp:+573102423332",  # Tu número de WhatsApp
            body=ai_reply
        )
    print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
        # Retornar una respuesta JSON
    return "Return: OK"

# Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])


