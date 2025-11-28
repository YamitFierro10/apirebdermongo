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

import os
from google import genai
from google.genai import types
from google.genai.errors import APIError
from .database import collection, obtener_archivo

# --- CONFIGURACIÓN ---

MODELO_GEMINI = "gemini-1.5-flash"
MAX_MENSAJES_HISTORIAL = 10
MAX_CARACTERES_AGRICOLA = 1500

PROMPT_AGRICOLA_BASE = """
Actúa como un ingeniero agrónomo con más de 20 años de experiencia en agricultura sostenible.
Analiza los datos proporcionados y brinda recomendaciones prácticas.

Datos del cultivo:
- Tipo de cultivo: {tipo_cultivo}
- Ubicación y clima: {ubicacion_clima}

Tu respuesta debe incluir:
1. Diagnóstico general.
2. Recomendaciones técnicas.
3. Buenas prácticas.
4. Calendario tentativo.

Responde en menos de {max_chars} caracteres.
"""

PROMPT_AGRICOLA_FINAL = PROMPT_AGRICOLA_BASE.format(
    tipo_cultivo="maíz blanco",
    ubicacion_clima="zona templada, lluvias frecuentes en abril y mayo",
    max_chars=MAX_CARACTERES_AGRICOLA
)

PROMPT_DOCUMENTOS = "Eres un experto creando documentos legales y contratos."
PROMPT_EXPLICACIONES = "Eres un asesor jurídico experto en explicar términos legales."
PROMPT_EDICION = "Eres un experto editando documentos legales existentes."

# ========================================================
# FUNCIÓN PRINCIPAL
# ========================================================

def get_ai_response(user_message, user_id):

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        return "Error: Falta la GEMINI_API_KEY."

    client = genai.Client(api_key=GEMINI_API_KEY)

    user_message_str = str(user_message).strip()
    user_message_lower = user_message_str.lower()

    mensajes_chat = []

    # --- HISTORIAL ---
    try:
        historial = list(
            collection.find(
                {"user_id": user_id},
                {"_id": 0, "role": 1, "content": 1}
            ).sort("_id", -1).limit(MAX_MENSAJES_HISTORIAL)
        )

        historial_ordenado = historial[::-1]

        for msg in historial_ordenado:
            mensajes_chat.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=msg["content"])]
                )
            )
    except Exception as e:
        print(f"⚠️ Error al recuperar historial MongoDB: {e}")

    # --- SELECCIÓN DE PROMPT ---
    if "hacer un contrato" in user_message_lower or "crear documento" in user_message_lower:
        prompt_system = PROMPT_DOCUMENTOS
    elif "qué significa" in user_message_lower or "explica" in user_message_lower:
        prompt_system = PROMPT_EXPLICACIONES
    elif "editar documento" in user_message_lower:
        prompt_system = PROMPT_EDICION
    else:
        prompt_system = PROMPT_AGRICOLA_FINAL

    # --- ARCHIVOS ---
    if "contrato de arrendamiento" in user_message_lower:
        archivo = obtener_archivo("Contrato de Arrendamiento")
        return archivo if archivo else "No encontré el archivo solicitado."

    # --- MENSAJE ACTUAL ---
    mensajes_chat.append(
        types.Content(role="user", parts=[types.Part(text=user_message_str)])
    )

    config = types.GenerateContentConfig(system_instruction=prompt_system)

    answer = "Hubo un error al generar la respuesta."

    # --- RESPUESTA GEMINI ---
    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=mensajes_chat,
            config=config
        )
        answer = response.text.strip()
    except APIError as e:
        print(f"⚠️ Error API Gemini: {e}")
        answer = "Error en la API de Gemini. Intenta de nuevo."
    except Exception as e:
        print(f"⚠️ Error desconocido: {e}")

    # --- GUARDAR HISTORIAL ---
    try:
        collection.insert_many([
            {"user_id": user_id, "role": "user", "content": user_message_str},
            {"user_id": user_id, "role": "assistant", "content": answer}
        ])
    except Exception as e:
        print(f"⚠️ Error guardando historial en MongoDB: {e}")

    return answer


