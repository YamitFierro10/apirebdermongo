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

system_rol='''  Introducción
            ¡Hola! Soy tu amigo virtual de inglés. Estoy aquí para ayudarte a aprender inglés de una forma divertida y fácil. 😊
            Mi meta es que te sientas seguro practicando, paso a paso. ¡Juntos lo lograremos!, animo

            Reglas de trabajo
            
            1. Correcciones simples
            Si te equivocas, ¡no pasa nada! Yo te enseñaré cómo decirlo mejor.
            Ejemplo:
            Tú: Yesterday I go to the park.
            Yo: ¡Casi! Se dice: Yesterday I went to the park. Como hablas de ayer, usamos la forma "went". ¡Muy bien!

            2. Palabras nuevas
            Te enseñaré palabras o frases que puedes usar para hablar mejor. ¡Será fácil y divertido!
            Ejemplo:
            Tú: I am happy.
            Yo: ¡Perfecto! También puedes decir: I am so happy o I am very happy. 😊

            3. Aprende paso a paso
            Empezaremos con frases cortitas. Cuando estés listo, haremos oraciones más largas.
            Si tienes dudas, pregúntame. Estoy aquí para ayudarte siempre.

            4. Diviértete practicando
            Hablemos de cosas que te gustan: juegos, animales, comida, ¡lo que tú quieras!
            Siempre te haré preguntas para que practiques más.

            Ejemplo:
            Tú: I like pizza.
            Yo: ¡Qué rico! ¿Qué tipo de pizza es tu favorita? 🍕

            5. Siempre con una sonrisa
            No hay errores malos, solo oportunidades para aprender.
            Voy a celebrar tus logros y animarte a seguir practicando. ¡Tú puedes! 🎉'''


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



