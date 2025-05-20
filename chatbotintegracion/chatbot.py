import openai
from .database import collection, obtener_archivo
import os

# Configurar API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🎯 Prompts especializados

PROMPT_AGRICOLA = """"
Actúa como un ingeniero agrónomo con más de 20 años de experiencia en agricultura sostenible y manejo de cultivos. 
Analiza los datos proporcionados y brinda recomendaciones técnicas claras y prácticas para optimizar la producción agrícola.

Datos del cultivo:
- Tipo de cultivo: 
- Ubicación y clima: 

Tu respuesta debe incluir:
1. Diagnóstico general de la situación.
2. Recomendaciones técnicas para mejorar la productividad.
3. Sugerencias sostenibles y buenas prácticas agrícolas.
4. Calendario tentativo de actividades si es posible.

Usa un lenguaje claro pero técnico, con enfoque práctico y orientado a resultados.
"""



PROMPT_DOCUMENTOS = "Tu tarea es ayudar a los usuarios a generar documentos legales como contratos..."
PROMPT_EXPLICACIONES = "Eres un experto en derecho y asesoras a los usuarios explicando términos legales..."
PROMPT_EDICION = "El usuario ha solicitado hacer cambios en un documento generado..."

def get_ai_response(user_message, user_id):
    """Genera una respuesta basada en la solicitud del usuario y ajusta el prompt según el contexto."""

    # ✅ Asegurar que `user_message` siempre sea una cadena antes de aplicar `.strip()`
    user_message = str(user_message).strip().lower()

    # 🔍 Intentar recuperar historial de conversación desde MongoDB
    mensajes = []
    try:
        historial = list(collection.find({"user_id": user_id}, {"_id": 0, "role": 1, "content": 1}))
        mensajes = [{"role": msg["role"], "content": msg["content"]} for msg in historial] if historial else []
    except Exception as e:
        print("⚠️ Error al conectar con MongoDB:", e)

    # 🔥 Selección del prompt adecuado
    if "hacer un contrato" in user_message or "crear documento" in user_message:
        prompt = PROMPT_DOCUMENTOS
    elif "qué significa" in user_message or "explica" in user_message:
        prompt = PROMPT_EXPLICACIONES
    elif "editar documento" in user_message or "cambiar información" in user_message:
        prompt = PROMPT_EDICION
    else:
        prompt = PROMPT_AGRICOLA

    # Agregar prompt al historial
    mensajes.insert(0, {"role": "system", "content": prompt})

    # 🗂️ Manejo de archivos
    if "contrato de arrendamiento" in user_message:
        archivo = obtener_archivo("Contrato de Arrendamiento")
        return "Aquí tienes tu contrato de arrendamiento. ¿Necesitas hacer cambios?" if archivo else "No encontré el archivo solicitado."

    # 🎯 Generar respuesta con OpenAI
    mensajes.append({"role": "user", "content": user_message})
    
    try:
        completar = openai.ChatCompletion.create(model="gpt-4", messages=mensajes)
        answer = completar['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("⚠️ Error al obtener respuesta de OpenAI:", e)
        return "Lo siento, ocurrió un problema al procesar tu solicitud."

    # 💾 Intentar guardar conversación en MongoDB (sin bloquear la respuesta)
    try:
        collection.insert_many([
            {"user_id": user_id, "role": "user", "content": user_message},
            {"user_id": user_id, "role": "assistant", "content": answer}
        ])
    except Exception as e:
        print("⚠️ No se pudo guardar en MongoDB:", e)

    return answer