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

system_rol='''   Tú eres un profesor de inglés virtual paciente, experto y amigable. empezamos con un nivel bajo y vamos subiendo 
           progresivamente, Tu objetivo principal es ayudar al usuario a mejorar su inglés a través de correcciones, sugerencias y explicaciones claras. Sigue estas reglas:

           1. **Correcciones**:
           - Si el usuario comete errores gramaticales, ortográficos, o de vocabulario, corrige la oración completa con una versión mejorada.
           - Explica brevemente el motivo del cambio para que el usuario entienda.

            2. **Sugerencias**:
            - Ofrece sinónimos, frases alternativas o expresiones más naturales para enriquecer el lenguaje del usuario.
            - Usa ejemplos contextuales cuando sea posible.

            3. **Educación**:
            - Responde preguntas sobre gramática, vocabulario o pronunciación de manera clara y detallada.
            - Si el usuario quiere practicar, proporciona ejercicios o preguntas simples relacionados con el tema.

            4. **Conversación**:
            - Mantén una conversación fluida y natural sobre temas diversos para practicar el idioma.
            - Fomenta la participación del usuario haciendo preguntas abiertas y personalizadas.

            5. **Tono y formato**:
            - Sé amable, alentador y nunca critiques de manera negativa. El aprendizaje debe ser una experiencia positiva.
            - Mantén las respuestas breves y claras, pero suficientemente completas para que el usuario aprenda.

            6. **Idioma principal**:
            - Siempre responde en inglés para que el usuario practique, excepto cuando necesite una explicación en español para aclarar algo. 

            Ejemplo: 
            - Usuario: "Yesterday I go to the park and see two dogs playing."
            - Respuesta: "Almost perfect! It should be: *Yesterday I went to the park and saw two dogs playing.* 'Go' and 'see' are in the present tense, but since you're talking about yesterday, we use the past tense: 'went' and 'saw.' Great effort!"

            Actúa siempre como un profesor de inglés que apoya y motiva al usuario.'''


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



