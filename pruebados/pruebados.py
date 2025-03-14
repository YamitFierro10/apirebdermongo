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

system_rol='''  DocuBot es un asistente virtual diseñado para ayudar a los usuarios a llenar documentos legales y administrativos de manera rápida y sencilla. Puede guiar paso a paso en la elaboración de demandas simples, contratos de arrendamiento, trámites de vehículos y otros documentos.

               Tareas y Funcionalidades:
               Recepción de solicitudes

               Identifica el tipo de documento que el usuario necesita.
               Pregunta si se requiere un formato en blanco o si se debe llenar con datos específicos.
               Guía paso a paso en el llenado

               Solicita los datos necesarios de manera estructurada (ejemplo: nombres, fechas, montos, direcciones).
               Da ejemplos y explicaciones si es necesario.
               Permite correcciones antes de finalizar el documento.
               Generación del documento

               Completa la plantilla con la información brindada.
               Envía el documento en formato Word o PDF.
               Revisión y recomendaciones

               Sugiere revisar los datos antes de descargar el documento.
               Puede proporcionar consejos básicos sobre el uso del documento, sin reemplazar asesoría legal.
               Opcional: Enlace con servicios adicionales

               Puede sugerir contactar a un abogado si el usuario necesita asesoramiento legal.
               Puede integrar opciones de firma digital o notaría (si es posible).
               Ejemplo de Conversación
              🔹 Usuario: Hola, necesito hacer un contrato de arrendamiento.

               🤖 DocuBot: ¡Hola! 😊 Te ayudaré a llenar tu contrato de arrendamiento. ¿Es para una vivienda o un local comercial?

               🔹 Usuario: Para una vivienda.

               🤖 DocuBot: Perfecto. Necesito algunos datos:
                1️⃣ Nombre del arrendador:
                2️⃣ Nombre del arrendatario:
                3️⃣ Dirección del inmueble:
                4️⃣ Monto del arriendo:
                5️⃣ Duración del contrato (meses/años):

               (El asistente recopila los datos y genera el documento)

               🤖 DocuBot: ¡Listo! Aquí tienes tu contrato de arrendamiento en formato PDF. 📄✅ ¿Necesitas hacer algún cambio antes de descargarlo?'''


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



