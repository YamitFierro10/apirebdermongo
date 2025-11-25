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
from .database import collection, obtener_archivo # Se asume que estos módulos existen

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---

# 🔒 Configurar la API Key de Gemini
# La clave se lee automáticamente de la variable de entorno GEMINI_API_KEY.
# Si estás usando la misma variable OPENAI_API_KEY, deberás renombrarla en el entorno.
try:
    client = genai.Client()
except Exception as e:
    print(f"⚠️ Error al inicializar el cliente Gemini: {e}")
    client = None

# ⚙️ Constantes de Configuración
MODELO_GEMINI = "gemini-2.5-flash"
MAX_CARACTERES_AGRICOLA = 1500 
MAX_MENSAJES_HISTORIAL = 10 

# 🎯 Definición de Prompts (Se mantienen iguales en contenido)
PROMPT_AGRICOLA_BASE = """" Actúa como un ingeniero agrónomo con más de 20 años de experiencia en agricultura sostenible y manejo de cultivos. 
Analiza los datos proporcionados y brinda recomendaciones técnicas claras y prácticas para optimizar la producción agrícola.
Datos del cultivo:
- Tipo de cultivo: {tipo_cultivo}
- Ubicación y clima: {ubicacion_clima}
Tu respuesta debe incluir:
1. Diagnóstico general de la situación.
2. Recomendaciones técnicas para mejorar la productividad.
3. Sugerencias sostenibles y buenas prácticas agrícolas.
4. Calendario tentativo de actividades si es posible.
Usa un lenguaje claro pero técnico, con enfoque práctico y orientado a resultados. contestar en menos de {max_chars} caracteres"""

PROMPT_DOCUMENTOS = "Tu tarea es ayudar a los usuarios a generar documentos legales como contratos..."
PROMPT_EXPLICACIONES = "Eres un experto en derecho y asesoras a los usuarios explicando términos legales..."
PROMPT_EDICION = "El usuario ha solicitado hacer cambios en un documento generado..."

# 🌐 Instancia del Prompt Agrícola
PROMPT_AGRICOLA_FINAL = PROMPT_AGRICOLA_BASE.format(
    tipo_cultivo="maíz blanco",
    ubicacion_clima="zona templada, lluvias frecuentes en abril y mayo",
    max_chars=MAX_CARACTERES_AGRICOLA
)

# ----------------------------------------

def get_ai_response(user_message, user_id):
    """Genera una respuesta basada en la solicitud del usuario usando la API de Google Gemini."""
    
    if client is None:
        return "Lo siento, la API de Gemini no se pudo inicializar correctamente."
    
    # 1. PREPROCESAMIENTO DEL MENSAJE
    user_message_str = str(user_message).strip()
    user_message_lower = user_message_str.lower()
    
    # 2. RECUPERAR HISTORIAL Y CONTEXTO
    mensajes_chat = []
    try:
        # Recuperar historial (N mensajes más recientes)
        historial = list(collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}).sort("_id", -1).limit(MAX_MENSAJES_HISTORIAL))
        historial_ordenado = historial[::-1] # Del más antiguo al más nuevo

        # Convertir el historial al formato "parts" de Gemini
        for msg in historial_ordenado:
            # Gemini usa 'user' y 'model' para roles en el historial
            role = "user" if msg["role"] == "user" else "model"
            mensajes_chat.append(
                types.Content(
                    role=role, 
                    parts=[types.Part.from_text(msg["content"])]
                )
            )

    except Exception as e:
        print(f"⚠️ Error al recuperar historial con MongoDB: {e}")

    # 3. SELECCIÓN DEL PROMPT DE SISTEMA
    if "hacer un contrato" in user_message_lower or "crear documento" in user_message_lower:
        prompt_system = PROMPT_DOCUMENTOS
    elif "qué significa" in user_message_lower or "explica" in user_message_lower:
        prompt_system = PROMPT_EXPLICACIONES
    elif "editar documento" in user_message_lower or "cambiar información" in user_message_lower:
        prompt_system = PROMPT_EDICION
    else:
        prompt_system = PROMPT_AGRICOLA_FINAL

    # 4. MANEJO DE ARCHIVOS (Lógica específica)
    if "contrato de arrendamiento" in user_message_lower:
        archivo = obtener_archivo("Contrato de Arrendamiento")
        return "Aquí tienes tu contrato de arrendamiento. ¿Necesitas hacer cambios?" if archivo else "No encontré el archivo solicitado."

    # 5. GENERAR RESPUESTA CON GEMINI

    # El mensaje del usuario actual se añade como el último mensaje.
    mensajes_chat.append(
        types.Content(
            role="user", 
            parts=[types.Part.from_text(user_message_str)]
        )
    )

    # Configuración de sistema (Instrucción inicial)
    config = types.GenerateContentConfig(
        system_instruction=prompt_system
    )
    
    answer = "Lo siento, ocurrió un problema al procesar tu solicitud."
    
    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI, 
            contents=mensajes_chat,
            config=config
        )
        answer = response.text.strip()
    except APIError as e:
        print(f"⚠️ Error de API de Gemini (Rate Limit/Auth): {e}")
        answer = "Lo siento, ocurrió un error en la conexión con la API de Gemini. Intenta de nuevo más tarde."
    except Exception as e:
        print(f"⚠️ Error desconocido al obtener respuesta de Gemini: {e}")

    # 6. GUARDAR CONVERSACIÓN
    try:
        collection.insert_many([
            {"user_id": user_id, "role": "user", "content": user_message_str},
            {"user_id": user_id, "role": "assistant", "content": answer}
        ])
    except Exception as e:
        print(f"⚠️ No se pudo guardar en MongoDB: {e}")

    return answer