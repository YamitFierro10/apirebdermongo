import openai
from .database import collection, obtener_archivo
import os

# Configurar API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🎯 Prompts especializados
PROMPT_GENERAL = "Eres DocuBot, un asistente experto en documentos legales y administrativos..."
PROMPT_DOCUMENTOS = "Tu tarea es ayudar a los usuarios a generar documentos legales como contratos..."
PROMPT_EXPLICACIONES = "Eres un experto en derecho y asesoras a los usuarios explicando términos legales..."
PROMPT_EDICION = "El usuario ha solicitado hacer cambios en un documento generado..."

def get_ai_response(user_message, user_id):
    """Genera una respuesta basada en la solicitud del usuario y ajusta el prompt según el contexto."""

    # ✅ Asegurar que `user_message` siempre sea una cadena antes de aplicar `.strip()`
    user_message = str(user_message).strip().lower()

    # 🔍 Buscar historial de conversación en MongoDB
    historial = list(collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}))
    mensajes = [{"role": msg["role"], "content": msg["content"]} for msg in historial] if historial else []

    # 🔥 Selección del prompt adecuado
    if "hacer un contrato" in user_message or "crear documento" in user_message:
        prompt = PROMPT_DOCUMENTOS
    elif "qué significa" in user_message or "explica" in user_message:
        prompt = PROMPT_EXPLICACIONES
    elif "editar documento" in user_message or "cambiar información" in user_message:
        prompt = PROMPT_EDICION
    else:
        prompt = PROMPT_GENERAL

    # Agregar prompt al historial
    mensajes.insert(0, {"role": "system", "content": prompt})

    # 🗂️ Manejo de archivos
    if "contrato de arrendamiento" in user_message:
        archivo = obtener_archivo("Contrato de Arrendamiento")
        return "Aquí tienes tu contrato de arrendamiento. ¿Necesitas hacer cambios?" if archivo else "No encontré el archivo solicitado."

    # 🎯 Generar respuesta con OpenAI
    mensajes.append({"role": "user", "content": user_message})
    completar = openai.ChatCompletion.create(model="gpt-4", messages=mensajes)
    answer = completar['choices'][0]['message']['content'].strip()

    # 💾 Guardar conversación en MongoDB
    collection.insert_many([
        {"user_id": user_id, "role": "user", "content": user_message},
        {"user_id": user_id, "role": "assistant", "content": answer}
    ])

    return answer

