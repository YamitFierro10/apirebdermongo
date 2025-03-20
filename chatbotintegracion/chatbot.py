import openai
from database import collection, obtener_archivo
import os

# Configurar API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🎯 Prompt General (Conversación abierta)
PROMPT_GENERAL = '''Eres DocuBot, un asistente experto en documentos legales y administrativos. 
Responde de manera clara y sencilla a cualquier pregunta relacionada con documentos, trámites y contratos.'''

# 📄 Prompt para Generación de Documentos
PROMPT_DOCUMENTOS = '''Tu tarea es ayudar a los usuarios a generar documentos legales como contratos de arrendamiento, 
cartas de renuncia, poderes notariales y más. 
Solicita los datos necesarios y estructura el documento de manera profesional.'''

# ⚖️ Prompt para Explicaciones Legales
PROMPT_EXPLICACIONES = '''Eres un experto en derecho y asesoras a los usuarios explicando términos legales de manera clara. 
Evita dar asesoramiento legal personalizado, pero proporciona información útil sobre el uso de cada documento.'''

# ✍️ Prompt para Edición de Documentos
PROMPT_EDICION = '''El usuario ha solicitado hacer cambios en un documento generado. 
Debes permitirle modificar partes específicas y asegurarte de que el documento final refleje sus correcciones.'''

def get_ai_response(user_message, user_id):
    """
    Genera una respuesta basada en la solicitud del usuario y ajusta el prompt según el contexto.
    """

    # 🔍 Buscar historial de conversación
    historial = list(collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}))
    mensajes = [{"role": msg["role"], "content": msg["content"]} for msg in historial]

    # 🔥 Determinar qué prompt usar según la solicitud del usuario
    if "hacer un contrato" in user_message.lower() or "crear documento" in user_message.lower():
        prompt = PROMPT_DOCUMENTOS
    elif "qué significa" in user_message.lower() or "explica" in user_message.lower():
        prompt = PROMPT_EXPLICACIONES
    elif "editar documento" in user_message.lower() or "cambiar información" in user_message.lower():
        prompt = PROMPT_EDICION
    else:
        prompt = PROMPT_GENERAL  # 🛠️ Respuesta estándar para otras preguntas

    # Agregar el prompt seleccionado
    mensajes.insert(0, {"role": "system", "content": prompt})

    # 🗂️ Manejo de archivos (si el usuario pide un documento específico)
    if "contrato de arrendamiento" in user_message.lower():
        archivo = obtener_archivo("Contrato de Arrendamiento")
        if archivo:
            return "Aquí tienes tu contrato de arrendamiento. ¿Necesitas hacer cambios antes de descargarlo?"
        else:
            return "Lo siento, no encontré el archivo que necesitas."

    # 🎯 Generar respuesta con OpenAI
    mensajes.append({"role": "user", "content": user_message})
    completar = openai.ChatCompletion.create(
        model="gpt-4",
        messages=mensajes
    )
    answer = completar['choices'][0]['message']['content'].strip()

    # 💾 Guardar conversación en MongoDB
    collection.insert_one({"user_id": user_id, "role": "user", "content": user_message})
    collection.insert_one({"user_id": user_id, "role": "assistant", "content": answer})

    return answer