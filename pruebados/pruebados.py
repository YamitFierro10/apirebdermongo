"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from fastapi import Request
import openai
from twilio.rest import Client
from dotenv import load_dotenv
import os
from pruebados.api import handle



class State(rx.State):
    """The app state."""

    ...

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configura las claves de API
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(twilio_sid, twilio_token)


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
def send_whatsapp_message(message):
    client.messages.create(
        from_="whatsapp:+14155238886",  # Cambia esto por tu número de Twilio para WhatsApp
        body=message,
        to="whatsapp:+573102423332"
    )

# Función para manejar mensajes entrantes de Twilio
async def handle_incoming_message(request: Request):
    
    data = await request.json()  # Extrae el JSON de la solicitud

    # Extraer la información relevante del JSON de Twilio
    incoming_msg = data.get('Body', '').strip()
    from_number = data.get('From', '')

    # Verificar que la información sea válida antes de proceder
    if incoming_msg and from_number:
        # Generar la respuesta AI usando OpenAI
        ai_reply = get_ai_response(incoming_msg)
        
        # Enviar la respuesta de vuelta al usuario por WhatsApp
        client.messages.create(
            from_="whatsapp:+14155238886",  # Número de Twilio
            body=ai_reply,
            to="whatsapp:+573102423332"  # Tu número de WhatsApp
        )
        print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
        # Retornar una respuesta JSON
        return {"status": "success", "response": ai_reply}
    else:
        print("Error: Mensaje entrante o número de remitente no encontrado.")
        return {"status": "error", "message": "Datos incompletos en la solicitud."}

# Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])


