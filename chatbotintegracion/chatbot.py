import os
import time
import requests
from time import time as now

from google.genai import types

# 🔥 cliente Gemini (inyectado desde main)
client = None

# =========================
# ⚡ CACHE
# =========================
cache = {}
CACHE_TTL = 300


# --- CONFIG ---
MODELO_GROQ = "llama-3.1-8b-instant"
MODELO_GEMINI = "gemini-2.5-flash"
MAX_RESPUESTA = 1500
MAX_MENSAJES_HISTORIAL = 10

# --- PROMPT PSICOLOGÍA (respuestas más cortas y conversadas) ---
PROMPT_PSICOLOGIA = """
Eres un Asistente de Apoyo agricola con enfasis en emociones, todo lo explicas con cultivos cuyo propósito es acompañar de manera cálida, cercana y segura. 
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

# =========================
# 🚦 RATE LIMIT
# =========================
user_last_request = {}

def is_rate_limited(user_id):
    t = now()
    if user_id in user_last_request:
        if t - user_last_request[user_id] < 2:
            return True
    user_last_request[user_id] = t
    return False


# =========================
# 🤖 GEMINI
# =========================
def responder_con_gemini(mensaje):
    global client

    if client is None:
        raise Exception("Gemini no disponible")

    mensajes = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=mensaje)]
        )
    ]

    config = types.GenerateContentConfig(system_instruction=PROMPT_PSICOLOGIA)

    response = client.models.generate_content(
        model=MODELO_GEMINI,
        contents=mensajes,
        config=config
    )

    try:
        return response.text
    except Exception:
        return str(response)


# =========================
# 🚀 GROQ (SIN LIBRERÍA)
# =========================
def responder_con_groq(mensaje):
    try:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            print("⚠️ GROQ_API_KEY no configurada")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODELO_GROQ,
            "messages": [
                {"role": "system", "content": PROMPT_PSICOLOGIA},
                {"role": "user", "content": mensaje}
            ]
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

        print("❌ Groq HTTP error:", response.text)
        return None

    except Exception as e:
        print("❌ Error Groq HTTP:", e)
        return None


# =========================
# 🧠 FUNCIÓN PRINCIPAL
# =========================
def get_ai_response(user_message, user_id):
    user_message_str = str(user_message).strip().lower()

    if not user_message_str:
        return "¿Puedes escribirme un poco más? 😊"

    # 🚦 rate limit
    if is_rate_limited(user_id):
        return "Dame un momento, ya te respondo 💬"

    # 🚨 crisis
    if any(p in user_message_str for p in CRISIS_KEYWORDS):
        return f"No tienes que pasar por esto solo. Aquí puedes buscar apoyo: {URL_APOYO}"

    # ⚡ cache
    if user_message_str in cache:
        data = cache[user_message_str]
        if now() - data["time"] < CACHE_TTL:
            print("⚡ Cache HIT")
            return data["response"]

    # =========================
    # 🔥 1. GEMINI (RETRY)
    # =========================
    for intento in range(2):
        try:
            print(f"🧠 Gemini intento {intento+1}")
            respuesta = responder_con_gemini(user_message_str)

            if respuesta:
                cache[user_message_str] = {
                    "response": respuesta,
                    "time": now()
                }
                return respuesta

        except Exception as e:
            print("❌ Gemini falló:", e)

            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("🚫 Sin cuota Gemini")
                break

            time.sleep(1)

    # =========================
    # 🚀 2. GROQ (FALLBACK)
    # =========================
    print("🚀 Usando Groq fallback")
    respuesta = responder_con_groq(user_message_str)

    if respuesta:
        return respuesta

    # =========================
    # 🧡 ÚLTIMO RESPALDO
    # =========================
    return "En este momento estoy un poco saturado, pero quiero escucharte. Cuéntame qué está pasando 💬"