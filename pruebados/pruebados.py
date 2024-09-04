"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import os
import reflex as rx
from openai import OpenAI
from fastapi import Request
from twilio.rest import Client
from dotenv import load_dotenv
from pruebados.api import handle


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str

DEFAULT_CHATS = {
    "Intros": [],
}

chats: dict[str, list[QA]] = DEFAULT_CHATS

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


# Configura las claves de API
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

system_rol='''Eres una asitente util'''


mensaje=[{"role": "system", "content": system_rol}]

def get_ai_response(respuesta):
    completar= OpenAI().chat.completions.create(
        model="gpt-4",
        messages=mensaje,
    )
    respuesta=completar.choices[0].message.content
    return respuesta

def handle_incoming_message():
    incoming_msg = Request.form["Body"]  # Extrae el mensaje
    ai_reply = get_ai_response(incoming_msg)
    
    # Generar la respuesta AI usando OpenAI
   
    client = Client(twilio_sid, twilio_token)
    from_number = Request.form["From"] # Extrae el número de remitente
        
    # Enviar la respuesta de vuelta al usuario por WhatsApp
    client.messages.create(
        from_="whatsapp:+14155238886",  # Número de Twilio
        body=ai_reply,
        to=from_number  # Tu número de WhatsApp 
    )
        
    # Retornar una respuesta JSON
    return "Return:OK"

#Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])


