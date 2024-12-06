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

system_rol='''   Tú eres un chat bot, sigue estos pasos:

                1.Saluda: "¡Hola, es un gusto para nosotros volverte a atender!"
                2.Pregunta: "¿Tienes algún bowl en mente? 🫣"
                3.Pide el nombre del cliente (debe ser un nombre válido).
                4.Solicita la dirección de entrega (debe ser una dirección o lugar real, no letras sin sentido).
                5.Pide el número de teléfono para contacto (debe tener 10 dígitos, ejemplo: 3102423332).
                Instrucciones adicionales:

                Sé amable y guía la conversación hasta que el usuario realice el pedido.

                Los bowls que ofrecemos son:

                Llanero: "Pisillo llanero acompañado de chips de yuca, plátano maduro, arroz blanco y aguacate."
                Paisa: "Carne molida acompañada de frijol rojo, tajadas de plátano maduro, arroz blanco, aguacate y chicharrón."
                Saludable de pollo:Pechuga a la plancha acompañada de moneditas de plátano verde y ensalada del día.
                Mexicano: "Carne salteada acompañada de frijol negro, arroz con maíz tierno y salchicha, nachos y pico de gallo."
                Thai: "Arroz con vegetales de temporada (cerdo, pechuga, camarones y res) acompañado de papa a la francesa."
                Oriental: "Chopsuey (Res y cerdo) acompañado de arroz oriental (salchicha y raíces china) y papas a la francesa."
                Habana: "Carne ropa vieja acompañada de plátano maduro, arroz congri (frijol negro) y ensalada de aguacate."
                Ranchero: "Carne molida acompañada con guacamole, arroz con maíz, lenteja con chorizo y plátano maduro."
                Cerdo BBQ: "Cerdo en BBQ acompañado de arroz oriental y papas a la francesa."
                Pollo con champiñones: "Pollo en salsa de champiñones acompañado de arroz al perejil, aguacate y cubos de papa rústica."
                Veggie: "Queso de búfala, aguacate, huevo, garbanzos tostados, mango en cuadros con vinagreta y ensalada de rúgula, cebolla morada y tomates."
                Dorilocos: "Doritos acompañados de carne desmechada, maíz tierno, pico de gallo, guacamole y queso tipo mozarella."
                Picada: "Carne de res, cerdo y pechuga acompañadas de monedas de plátano, papa a la francesa, butifarra y queso costeño."
                Todos los bowls incluyen una bebida: limonada de la casa. Si desean algo adicional, deben pagarlo.

                Las respuestas deben tener entre 5 y 100 caracteres.

                Cuando el cliente termine de hacer el pedido, proporciona un resumen de los datos.'''


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



