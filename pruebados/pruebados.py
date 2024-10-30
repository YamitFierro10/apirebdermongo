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

system_rol='''Eres una asitente util responde las preguntas que tenga el usuario'''


mensaje=[{"role": "system", "content": system_rol}]

def get_ai_response(respuesta):
    completar= OpenAI().chat.completions.create(
        model="gpt-4",
        messages=mensaje,
    )
    respuesta=completar.choices[0].message.content
    return respuesta

def handle_incoming_message():
    incoming_msg= Request.form['Body']  # Extrae el formulario de la solicitud
   # incoming_msg = form.get("Body")  # Extrae el mensaje
   #from_number = form.get("From")  # Extrae el número de remitente

    # Generar la respuesta AI usando OpenAI
    ai_reply = get_ai_response(incoming_msg)
    client = Client(twilio_sid, twilio_token)
    from_number= Request.form['From']
        
    # Enviar la respuesta de vuelta al usuario por WhatsApp
    client.messages.create(
        from_="whatsapp:+14155238886",  # Número de Twilio
        body=ai_reply,
        to=from_number  # Tu número de WhatsApp 
    )
    print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
    # Retornar una respuesta JSON
    return {"status": "success", "response": ai_reply}

#Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])


