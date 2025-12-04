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
from google.genai.errors import APIError
from .database import collection

# --- CONFIG ---
MODELO_GEMINI = "gemini-2.0-flash"
MAX_RESPUESTA = 1500
MAX_MENSAJES_HISTORIAL = 10

# --- PROMPT PSICOLOGÍA ---
PROMPT_PSICOLOGIA = """
Eres un asistente de apoyo emocional diseñado especialmente para acompañar a personas jóvenes.
Tu rol es escuchar, validar y ofrecer estrategias seguras y sencillas de bienestar como respiración,
grounding, autocuidado y comunicación asertiva. No das diagnósticos, no describes autolesiones
y no sustituyes apoyo profesional.

Reglas:
1. Usa un tono cálido, empático, cercano y claro.
2. No utilices etiquetas clínicas ni diagnósticos.
3. No describas ni detalles autolesiones en ningún contexto.
4. Si notas angustia alta, valida, acompaña y anima a buscar ayuda de un adulto o profesional.
5. Ofrece máximo 1 o 2 técnicas simples por respuesta.
6. Tu prioridad es que la persona se sienta escuchada y acompañada.
"""

# --- MENSAJE DE BIENVENIDA (cuando no se detecta intención clara) ---
MENSAJE_BIENVENIDA = """
Estoy aquí para escucharte y acompañarte. Si tienes algo en mente, si te sientes confundido,
triste, abrumado o simplemente quieres desahogarte, puedes hacerlo conmigo. Este es un espacio
seguro para ti.

Puedo ayudarte a explorar cómo te sientes, validar tus emociones y compartirte técnicas simples
para sentirte un poco mejor. ¿Cómo te has estado sintiendo hoy?
"""

# --- PALABRAS CLAVE PARA DETECTAR CASO CRÍTICO ---
CRISIS_KEYWORDS = [
    "no puedo más",
    "ya no puedo",
    "me siento muy mal",
    "estoy desesperado",
    "estoy desesperada",
    "nadie me entiende",
    "me siento solo",
    "me siento sola",
    "me siento vacío",
    "me siento vacía",
    "quiero rendirme",
    "todo está mal",
    "estoy muy triste",
    "estoy angustiado",
    "estoy angustiada",
]

# --- URL DE APOYO ---
URL_APOYO = "https://www.doctoralia.co/search-assistant?specialization_name=psychology"


# -----------------------------------------------------------------
# 🧠 FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------

def get_ai_response(user_message, user_id):

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        return "Error: falta configurar GEMINI_API_KEY en el servidor."

    client = genai.Client(api_key=GEMINI_API_KEY)

    user_message_str = str(user_message).strip().lower()

    # 1. DETECCIÓN DE CASO CRÍTICO
    if any(p in user_message_str for p in CRISIS_KEYWORDS):
        return (
            "Siento que estás pasando por un momento muy difícil y no tienes que enfrentar eso solo/a. "
            "Hablar con un adulto de confianza o un profesional puede ayudarte muchísimo. "
            "Si puedes, busca apoyo ahora mismo. También puedes encontrar ayuda aquí:\n\n"
            f"{URL_APOYO}"
        )

    # 2. Cargar historial
    mensajes_chat = []
    try:
        historial = list(
            collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1})
            .sort("_id", -1).limit(MAX_MENSAJES_HISTORIAL)
        )
        historial_ordenado = historial[::-1]

        for msg in historial_ordenado:
            part = types.Part.from_text(text=msg.get("content", ""))
            role = "user" if msg["role"] == "user" else "model"
            mensajes_chat.append(types.Content(role=role, parts=[part]))

    except Exception as e:
        print(f"⚠️ Error historial: {e}")

    # 3. Si solo saludan o no hay intención clara → mensaje de bienvenida
    if user_message_str in ["hola", "buenas", "hey", "qué haces", "que haces", "holi", "ola"]:
        return MENSAJE_BIENVENIDA.strip()

    # 4. Usar prompt psicológico
    prompt_system = PROMPT_PSICOLOGIA

    # 5. Agregar mensaje actual
    mensajes_chat.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message_str)]
    ))

    config = types.GenerateContentConfig(system_instruction=prompt_system)

    # 6. Generar respuesta
    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=mensajes_chat,
            config=config
        )
        answer = getattr(response, "text", "") or str(response)

    except Exception as e:
        print(f"⚠️ Error generando respuesta: {e}")
        answer = "Hubo un problema al procesar lo que dijiste, pero aquí estoy para escucharte."

    # 7. Limitar respuesta (antes de guardar)
    if len(answer) > MAX_RESPUESTA:
        answer = answer[:MAX_RESPUESTA] + "..."

    # 8. Guardar historial
    try:
        collection.insert_many([
            {"user_id": user_id, "role": "user", "content": user_message},
            {"user_id": user_id, "role": "assistant", "content": answer}
        ])
    except Exception as e:
        print(f"⚠️ Error guardando historial: {e}")

    return answer




