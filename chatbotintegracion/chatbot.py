# import openai
# from .database import collection, obtener_archivo
# import os

# # Configurar API Key de OpenAI
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # 🎯 Prompts especializados

# prompt_a = """" Actúa como un ingeniero agrónomo con más de 20 años de experiencia en agricultura sostenible y manejo de cultivos. 
# Analiza los datos proporcionados y brinda recomendaciones técnicas claras y prácticas para optimizar la producción agrícola.
# Datos del cultivo:
# - Tipo de cultivo: {tipo_cultivo}
# - Ubicación y clima: {ubicacion_clima}
# Tu respuesta debe incluir:
# 1. Diagnóstico general de la situación.
# 2. Recomendaciones técnicas para mejorar la productividad.
# 3. Sugerencias sostenibles y buenas prácticas agrícolas.
# 4. Calendario tentativo de actividades si es posible.
# Usa un lenguaje claro pero técnico, con enfoque práctico y orientado a resultados. contestar en menos de 1500 caracteres"""

# PROMPT_AGRICOLA = prompt_a.format(
#     tipo_cultivo="maíz blanco",
#     ubicacion_clima="zona templada, lluvias frecuentes en abril y mayo"
# )
# PROMPT_DOCUMENTOS = "Tu tarea es ayudar a los usuarios a generar documentos legales como contratos..."
# PROMPT_EXPLICACIONES = "Eres un experto en derecho y asesoras a los usuarios explicando términos legales..."
# PROMPT_EDICION = "El usuario ha solicitado hacer cambios en un documento generado..."

# def get_ai_response(user_message, user_id):
#     """Genera una respuesta basada en la solicitud del usuario y ajusta el prompt según el contexto."""

#     # ✅ Asegurar que `user_message` siempre sea una cadena antes de aplicar `.strip()`
#     user_message = str(user_message).strip().lower()

#     # 🔍 Intentar recuperar historial de conversación desde MongoDB
#     mensajes = []
#     try:
#         historial = list(collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}))
#         mensajes = [{"role": msg["role"], "content": msg["content"]} for msg in historial] if historial else []
#     except Exception as e:
#         print("⚠️ Error al conectar con MongoDB:", e)

#     # 🔥 Selección del prompt adecuado
#     if "hacer un contrato" in user_message or "crear documento" in user_message:
#         prompt = PROMPT_DOCUMENTOS
#     elif "qué significa" in user_message or "explica" in user_message:
#         prompt = PROMPT_EXPLICACIONES
#     elif "editar documento" in user_message or "cambiar información" in user_message:
#         prompt = PROMPT_EDICION
#     else:
#         prompt = PROMPT_AGRICOLA

#     # Agregar prompt al historial
#     mensajes.insert(0, {"role": "system", "content": prompt})

#     # 🗂️ Manejo de archivos
#     if "contrato de arrendamiento" in user_message:
#         archivo = obtener_archivo("Contrato de Arrendamiento")
#         return "Aquí tienes tu contrato de arrendamiento. ¿Necesitas hacer cambios?" if archivo else "No encontré el archivo solicitado."

#     # 🎯 Generar respuesta con OpenAI
#     mensajes.append({"role": "user", "content": user_message})
    
#     try:
#         completar = openai.ChatCompletion.create(model="gpt-4", messages=mensajes)
#         answer = completar['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         print("⚠️ Error al obtener respuesta de OpenAI:", e)
#         return "Lo siento, ocurrió un problema al procesar tu solicitud."

#     # 💾 Intentar guardar conversación en MongoDB (sin bloquear la respuesta)
#     try:
#         collection.insert_many([
#             {"user_id": user_id, "role": "user", "content": user_message},
#             {"user_id": user_id, "role": "assistant", "content": answer}
#         ])
#     except Exception as e:
#         print("⚠️ No se pudo guardar en MongoDB:", e)

#     return answer


# import os
# from google import genai
# from google.genai import types
# from google.genai.errors import APIError
# from .database import collection

# # --- CONFIG y CONSTANTES ---
# MODELO_GEMINI = "gemini-2.0-flash"
# MAX_CARACTERES_AGRICOLA = 1500
# MAX_MENSAJES_HISTORIAL = 10

# # --- PROMPT ÚNICO Y CENTRAL ---
# PROMPT_AGRICOLA = """
# Eres un ingeniero agrónomo con más de 20 años de experiencia.
# Responde únicamente sobre agricultura. Si el usuario pide otra cosa,
# redirígelo amablemente a que especifique un cultivo.

# Reglas:
# - Enfócate SOLO en el cultivo indicado.
# - NO cambies el tema.
# - Máximo {max_chars} caracteres.
# - Resume si es necesario para no exceder el límite.

# Datos detectados:
# - Cultivo: {cultivo}
# - Ubicación y clima: {ubicacion_clima}

# Estructura de la respuesta:
# 1. Diagnóstico general.
# 2. Recomendaciones técnicas prácticas.
# 3. Buenas prácticas sostenibles.
# 4. Actividades sugeridas si corresponde.

# Mensaje del usuario:
# {mensaje}
# """

# # -------------------------------------------------------
# # 🔍 DETECTORES
# # -------------------------------------------------------

# def detectar_cultivo(mensaje):
#     cultivos = [
#         "maíz", "maiz", "arroz", "café", "cafe", "cacao", "plátano", "platano",
#         "banano", "papa", "yuca", "tomate", "cebolla", "frijol", "soya",
#         "algodón", "algodon", "trigo", "limón", "lima", "aguacate", "mango",
#         "hortalizas", "pastos", "caña", "caña de azúcar", "fresa"
#     ]
#     msg = mensaje.lower()
#     for c in cultivos:
#         if c in msg:
#             return c
#     return None


# def detectar_clima(mensaje):
#     climas = {
#         "clima frío": ["frio", "frío"],
#         "clima templado": ["templado"],
#         "clima cálido": ["calido", "cálido", "tropical"],
#         "lluvias frecuentes": ["lluvia", "lluvioso", "invierno", "llueve"],
#         "época seca": ["verano", "seco", "sequía"]
#     }
#     msg = mensaje.lower()
#     result = []

#     for nombre, palabras in climas.items():
#         for p in palabras:
#             if p in msg:
#                 result.append(nombre)

#     return ", ".join(result) if result else None


# def detectar_ubicacion(mensaje):
#     ubicaciones = [
#         "meta", "cundinamarca", "tolima", "huila", "santander",
#         "nariño", "cauca", "antioquia", "cesar", "magdalena",
#         "guaviare", "putumayo", "caquetá", "córdoba"
#     ]
#     msg = mensaje.lower()
#     for u in ubicaciones:
#         if u in msg:
#             return u.capitalize()
#     return None


# # -------------------------------------------------------
# # 🧠 GENERADOR PRINCIPAL
# # -------------------------------------------------------

# def get_ai_response(user_message, user_id):

#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#     if not GEMINI_API_KEY:
#         return "Error: falta configurar GEMINI_API_KEY."

#     client = genai.Client(api_key=GEMINI_API_KEY)

#     mensaje = str(user_message).strip()
#     mensaje_lower = mensaje.lower()

#     # --- Recuperar historial ---
#     mensajes_chat = []
#     try:
#         historial = list(
#             collection.find(
#                 {"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}
#             ).sort("_id", -1).limit(MAX_MENSAJES_HISTORIAL)
#         )

#         historial_ordenado = historial[::-1]

#         for msg in historial_ordenado:
#             part = types.Part.from_text(text=msg.get("content", ""))
#             mensajes_chat.append(types.Content(role=msg.get("role"), parts=[part]))

#     except Exception as e:
#         print(f"⚠️ MongoDB historial error: {e}")

#     # --- Detectar datos agrícolas ---
#     cultivo = detectar_cultivo(mensaje_lower)
#     clima = detectar_clima(mensaje_lower)
#     ubicacion = detectar_ubicacion(mensaje_lower)

#     # Si no hay nada agrícola → pedir cultivo
#     if not cultivo:
#         return (
#             "Para ayudarte como agrónomo, por favor dime el cultivo que deseas consultar "
#             "(ej: maíz, arroz, tomate, café...)."
#         )

#     # Construir datos combinados
#     ubicacion_clima = (
#         f"Ubicación: {ubicacion if ubicacion else 'no detectada'}, "
#         f"Clima: {clima if clima else 'no detectado'}"
#     )

#     # Generar prompt final agrícola
#     prompt_system = PROMPT_AGRICOLA.format(
#         cultivo=cultivo,
#         ubicacion_clima=ubicacion_clima,
#         max_chars=MAX_CARACTERES_AGRICOLA,
#         mensaje=mensaje
#     )

#     # Añadir mensaje actual
#     mensajes_chat.append(types.Content(
#         role="user",
#         parts=[types.Part.from_text(text=mensaje)]
#     ))

#     config = types.GenerateContentConfig(system_instruction=prompt_system)

#     # Llamar a Gemini
#     try:
#         response = client.models.generate_content(
#             model=MODELO_GEMINI,
#             contents=mensajes_chat,
#             config=config
#         )
#         answer = getattr(response, "text", "") or str(response)

#     except Exception as e:
#         print(f"⚠️ Gemini error: {e}")
#         answer = "Hubo un problema generando la respuesta."

#     answer = answer.strip()

#     # --- Limitar por Twilio ---
#     if len(answer) > 1500:
#         answer = answer[:1500] + "..."

#     # Guardar historial
#     try:
#         collection.insert_many([
#             {"user_id": user_id, "role": "user", "content": mensaje},
#             {"user_id": user_id, "role": "assistant", "content": answer}
#         ])
#     except Exception as e:
#         print(f"⚠️ Error guardando historial MongoDB: {e}")

#     return answer

import os
from google import genai
from google.genai import types
from .database import collection
import traceback

# --- CONFIG ---
MODELO_GEMINI = "gemini-2.0-flash"
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

    client = chatbot_module.client

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




