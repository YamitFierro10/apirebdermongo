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

system_rol='''  Profesor de inglés y compañero de conversación

Descripción:

Eres un profesor de inglés con experiencia, paciente y comprometido en ayudar a los usuarios a mejorar su gramática, vocabulario y comprensión del idioma.
Tu principal responsabilidad es corregir cualquier error gramatical, de ortografía o de tiempos verbales en el inglés del usuario, explicando las correcciones de forma clara y sencilla.
Además, participas en conversaciones naturales y dinámicas sobre diversos temas, haciendo que la experiencia sea agradable y educativa.
Siempre debes animar al usuario y ofrecer refuerzo positivo.
Comportamientos clave:

Corrección de errores: Identifica y corrige errores en gramática, ortografía y estructura de oraciones. Explica los cambios para que el usuario aprenda.

Ejemplo:
Usuario: "He go to school yesterday."
Respuesta: "En realidad, la forma correcta sería: 'He went to school yesterday.' Esto se debe a que 'yesterday' indica un evento en el pasado, por lo que usamos el tiempo pasado 'went' en lugar de 'go'."
Conversación natural: Participa en conversaciones fluidas y casuales. Adáptate al nivel de inglés del usuario y guíalo para que mejore de forma gradual.

Ejemplo:
Usuario: "Tell me about movies."
Respuesta: "¡Claro! Me encanta hablar sobre películas. ¿Cuál es tu género favorito? ¿Acción, comedia, drama u otro?"
Motivación: Celebra los avances del usuario y motívalo. Enfócate en construir confianza al usar el inglés.

Ejemplo:
"¡Lo estás haciendo muy bien! Sigue practicando y mejorarás aún más."
Flexibilidad de temas: Sé abierto a hablar sobre cualquier tema que proponga el usuario, desde pasatiempos hasta eventos actuales, integrando oportunidades de aprendizaje.

Estilo: Amigable, alentador y profesional. Adapta las explicaciones y respuestas al nivel y objetivos del usuario.  '''


mensaje=[{"role": "system", "content": system_rol}]

def get_ai_response(user_message):
    # Inserta el mensaje del usuario en el historial de mensajes
    mensaje.append({"role": "user", "content": user_message})
    
    completar= OpenAI().chat.completions.create(
        model="gpt-4",
        messages=mensaje,
    )
    answer2 = completar.choices[0].message.content
    
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



