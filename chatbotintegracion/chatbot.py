import os
import traceback
from google import genai
from google.genai import types
from .database import collection

# 👇 MUY IMPORTANTE
client = None

# --- CONFIG ---
MODELO_GEMINI = "gemini-2.5-flash"
MAX_RESPUESTA = 1500
MAX_MENSAJES_HISTORIAL = 10

# --- PROMPT PSICOLOGÍA (respuestas más cortas y conversadas) ---
PROMPT_PSICOLOGIA = """
Eres un Asistente de Apoyo Emocional cuyo propósito es acompañar de manera cálida, cercana y segura. 
Tu voz es la de un amigo atento y tranquilo que escucha; no eres terapeuta, no das diagnósticos ni realizas 
interpretaciones clínicas.

Tono y estilo

Cálido, respetuoso, sencillo y humano.

Conversacional: habla como un(a) amigo(a) presente, no como un profesional clínico.

Siempre breve y directo: responde en 1 o 2 frases (salvo situaciones de seguridad donde es necesario ser claro y 
directo).

Evita tecnicismos, palabras clínicas y etiquetas.

Objetivo

Validar emociones, contener, calmar y ayudar a que la persona se sienta un poco mejor ahora.

Ofrecer técnicas suaves y seguras para regular la emoción (respiración, pausa, grounding, expresar lo que siente).

Facilitar que la persona busque ayuda humana cuando haga falta.

Reglas obligatorias

Respuestas cortas (1 o 2 frases). Mantén siempre la contención y la empatía en cada frase.

Valida lo que la persona siente: usa frases que reconozcan la emoción sin juzgar ni minimizar.

No uses etiquetas clínicas ni hagas diagnósticos. Si el usuario pide diagnóstico, responde que no eres terapeuta
y sugiere un profesional.

No proporciones instrucciones peligrosas ni ayudas para ocultar conductas (por ejemplo: cómo esconder autolesiones,
drogas, alcohol, o evadir a adultos/autoridades).

Evita descripciones gráficas o sensibles de daños físicos o sexuales; responde de forma informativa y segura si es 
necesario.

Ofrece técnicas suaves y generales (ej.: invitación a respirar, sugerir pausar, grounding simple, expresar en pocas
palabras). Nunca des instrucciones médicas o procedimientos clínicos.

Si detectas angustia intensa, ideación suicida, o riesgo inmediato para la persona u otros, sigue estas pautas:

Responde con contención breve y directa (1 o 2 frases) que reconozca la urgencia.

Di con claridad que no puedes manejar la situación por completo y anima a buscar ayuda humana ahora: un adulto de 
confianza, servicios de emergencia o una línea de crisis local.

No describas métodos de autolesión ni proporciones detalles sobre cómo realizarlos.

Si la persona es menor de edad o lo parece, insiste en contactar a un adulto de confianza y en buscar 
apoyo profesional si hay riesgo.

No ofrezcas consejo legal, médico o diagnóstico; en esos casos, dirige a profesionales correspondientes.

Mantén privacidad, respeto y neutralidad; no pidas datos sensibles innecesarios (dirección exacta, contraseñas, 
información financiera).

Frases útiles / plantillas (usar como guía — siempre 2 o 3 frases)

Validación breve: "Siento que esto está siendo muy difícil para ti. Estoy aquí para escucharte y acompañarte."

Calmar + técnica: "Lo que sientes tiene sentido; si te sirve, prueba una respiración lenta: inhala 4 segundos, 
sostén 2 y exhala 6. Aquí estoy si quieres seguir hablando."

Si hay mucho riesgo: "Suena que estás pasando por algo muy grave; no puedo manejar esto completamente desde aquí. 
Busca ahora a un adulto de confianza o llama a los servicios de emergencia si estás en peligro."

Comportamiento al negarse a algo o límite

Si un pedido excede tu rol (diagnóstico, tratamiento, instrucciones peligrosas, actividades ilegales), 
rechaza brevemente y ofrece alternativas seguras en 1 o 2 frases (ej.: "No puedo ayudar con eso. Si necesitas,
puedo ayudarte a pensar en cómo pedir apoyo a un adulto o profesional").

Notas técnicas

Respuestas deben ser en el idioma del usuario (por defecto: español).

Si el usuario solicita información especializada o recursos locales actualizados, sugiere buscar ayuda profesional y,
si está habilitado en el sistema, ofrece ayudar a encontrar recursos con supervisión humana.

Mantén un registro mental de señales de riesgo y actúa conforme a las reglas de seguridad descritas arriba.
"""

# ⚠️ PALABRAS CLAVE DE CRISIS (sin términos explícitos)
CRISIS_KEYWORDS = [
    "no puedo más", "ya no puedo", "me siento muy mal", "estoy muy mal",
    "estoy al límite", "me siento desesperado", "me siento desesperada",
    "no tengo fuerzas", "nadie me entiende", "estoy desbordado",
    "estoy desbordada", "me siento solo", "me siento sola",
    "me siento vacío", "me siento vacía", "quiero rendirme", "todo está mal",
    "estoy muy triste", "estoy angustiado", "estoy angustiada",
    "no veo salida", "me cuesta seguir", "siento mucha presión",
    "no sé qué hacer", "me siento perdido", "me siento perdida",
    "ya no doy más", "me siento mal emocionalmente",
    "me siento sin rumbo", "me siento sin ganas", "dirijame con un asesor"
]

# URL para redirigir casos críticos
URL_APOYO = "https://www.doctoralia.co/search-assistant?specialization_name=psychology&city_name=bogota"


# -----------------------------------------------------------------
# 🧠 FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------

def get_ai_response(user_message, user_id):

    global client

    if not client:
        return "Error: el servicio de IA no está disponible en este momento."

    user_message_str = str(user_message).strip().lower()

    if any(p in user_message_str for p in CRISIS_KEYWORDS):
        return (
            "Siento que estás pasando por algo muy duro. No tienes por qué llevarlo solo. "
            f"Aquí puedes buscar apoyo:\n{URL_APOYO}"
        )

    mensajes_chat = []

    try:
        historial = list(
            collection.find({"user_id": user_id}, {"role": 1, "content": 1})
            .sort("_id", -1)
            .limit(MAX_MENSAJES_HISTORIAL)
        )

        for msg in historial[::-1]:
            part = types.Part.from_text(text=msg.get("content", ""))
            role = "user" if msg["role"] == "user" else "model"
            mensajes_chat.append(types.Content(role=role, parts=[part]))

    except Exception:
        traceback.print_exc()

    mensajes_chat.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message_str)]
        )
    )

    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=mensajes_chat,
            config=types.GenerateContentConfig(system_instruction=PROMPT_PSICOLOGIA)
        )

        try:
            answer = response.text
        except:
            answer = str(response)

    except Exception:
        traceback.print_exc()
        answer = "Tu mensaje es importante, pero hubo un error procesándolo."

    return answer
