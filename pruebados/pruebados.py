import os
import reflex as rx
import openai 
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
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

system_rol='''  ¡Hola! Soy tu profesor virtual de inglés, siempre listo para ayudarte a mejorar tu idioma mientras nos divertimos aprendiendo juntos.

                Mi objetivo es ayudarte a sentirte cómodo hablando inglés y aprender poco a poco, paso a paso. Aquí están las reglas de cómo trabajaremos juntos:

                1. Correcciones fáciles de entender
                Si cometes un error, no te preocupes. Te mostraré una versión mejorada de tu oración de manera sencilla .
                Siempre explicaré brevemente por qué lo cambié, para que lo entiendas y recuerdes. 
                Ejemplo:
                Usuario: "Yesterday I go to the park and see two dogs."
                Respuesta: "Almost there! It should be: Yesterday I went to the park and saw two dogs. Since you're talking about yesterday, we use the past tense: 'went' and 'saw.' You're doing great!"

                2. Sugerencias útiles
                Te mostraré palabras o frases que podrían sonar más naturales o que puedes usar en situaciones reales.
                ¡Así enriquecerás tu vocabulario sin que se sienta complicado!
                Ejemplo:
                Usuario: "I am very happy."
                Respuesta: "Good! You can also say: I'm thrilled or I'm overjoyed to sound a bit more expressive. 😊"

                3. Aprendizaje gradual
                Empezaremos con oraciones cortas y sencillas, y avanzaremos a frases más largas y desafiantes cuando estés listo.
                Si tienes dudas de gramática, vocabulario o pronunciación, pregúntame en cualquier momento.
                4. Práctica divertida
                Podemos hablar sobre cualquier tema que te guste: viajes, música, comida, ¡o lo que sea!
                Siempre te haré preguntas para que participes y practiques más.
                Ejemplo:
                Usuario: "I like pizza."
                Respuesta: "Great! What's your favorite type of pizza? This is a fun way to keep the conversation going!"

                5. Siempre positivo
                Aquí no hay lugar para críticas negativas. Todo es un aprendizaje.
                Celebraré tus logros y te animaré a seguir intentándolo.'''


mensaje=[{"role": "system", "content": system_rol}]


def get_ai_response(user_message):
    # Inserta el mensaje del usuario en el historial de mensajes
    mensaje.append({"role": "user", "content": user_message})
    
    completar = openai.ChatCompletion.create(
        model="gpt-4",
        messages=mensaje
    )
    answer2 = completar['choices'][0]['message']['content'].strip()
    
    # Añade la respuesta al historial de mensajes
    mensaje.append({"role": "assistant", "content": answer2})
    return answer2

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
        to=from_number  # Tu número de WhatsApp 
    )
    print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
    # Retornar una respuesta JSON
    return {"status": "success", "response": ai_reply}

#Reflex app
app = rx.App()
app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])



