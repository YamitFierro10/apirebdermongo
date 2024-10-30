import os
import reflex as rx
import openai
from fastapi import FastAPI, Request
from twilio.rest import Client
from dotenv import load_dotenv
from pruebados.api import handle

class QA(rx.Base):
    """Par de preguntas y respuestas."""
    question: str
    answer: str

# Chats predeterminados
DEFAULT_CHATS = {"Intros": []}
chats: dict[str, list[QA]] = DEFAULT_CHATS

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar las claves de API
openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# Inicializar cliente de Twilio fuera de la función para evitar recargas
client = Client(twilio_sid, twilio_token)

# Definir el rol del sistema para OpenAI
system_role = "Eres un asistente útil. Responde a las preguntas que tenga el usuario."
mensaje = [{"role": "system", "content": system_role}]

def get_ai_response(user_message: str) -> str:
    """Genera una respuesta usando la API GPT-4."""
    # Añadir el mensaje del usuario a la conversación
    mensaje.append({"role": "user", "content": user_message})
    
    try:
        # Realizar la llamada a la API de OpenAI
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=mensaje
        )
        # Obtener la respuesta del asistente
        return completion.choices[0].message["content"]
    
    except Exception as e:
        print(f"Error al obtener la respuesta de OpenAI: {e}")
        return "Lo siento, hubo un problema al generar la respuesta."

async def handle_incoming_message(request: Request):
    """Maneja los mensajes entrantes desde WhatsApp."""
    # Extraer los datos del formulario de la solicitud entrante
    form = await request.form()
    incoming_msg = form.get("Body")
    from_number = form.get("From")

    # Generar la respuesta de OpenAI
    ai_reply = get_ai_response(incoming_msg)

    # Enviar la respuesta al usuario vía WhatsApp usando Twilio
    client.messages.create(
        from_="whatsapp:+14155238886",  # Número de Twilio para WhatsApp
        body=ai_reply,
        to=from_number  # Número del usuario
    )
    print(f"Mensaje enviado a {from_number}: {ai_reply}")

    # Retornar una respuesta JSON
    return {"status": "success", "response": ai_reply}

# Crear instancias de FastAPI y Reflex
fastapi_app = FastAPI()
app = rx.App()

# Agregar las rutas de FastAPI
fastapi_app.add_api_route("/handle", handle)
fastapi_app.add_api_route("/whatsapp", handle_incoming_message, methods=["POST"])

# Montar la aplicación FastAPI dentro de Reflex
app.api.mount("/api", fastapi_app)
