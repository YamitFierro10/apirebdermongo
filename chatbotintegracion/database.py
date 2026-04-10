import os
import certifi
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 🔥 variables
MONGO_URI = os.getenv("MONGO_URI")

# 🔥 conexión segura
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    client.admin.command("ping")
    print("✅ Conectado a MongoDB correctamente")
except Exception as e:
    print("❌ Error conectando MongoDB:", e)
    client = None

# 🔹 base de datos
if client:
    client_db = client["chatbot_db"]
    collection = client_db["conversaciones"]
    fs = gridfs.GridFS(client_db)
else:
    client_db = None
    collection = None
    fs = None


# =========================
# 📁 GRIDFS FUNCTIONS
# =========================

def guardar_archivo(ruta_archivo, nombre_archivo):
    """Guarda archivo en MongoDB GridFS"""
    if fs is None:
        return None

    try:
        with open(ruta_archivo, "rb") as archivo:
            archivo_id = fs.put(archivo, filename=nombre_archivo)

        print(f"📁 Archivo guardado: {nombre_archivo}")
        return archivo_id

    except Exception as e:
        print("❌ Error guardando archivo:", e)
        return None


def obtener_archivo(nombre_archivo):
    """Obtiene archivo desde GridFS"""
    if fs is None:
        return None

    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        return archivo.read() if archivo else None

    except Exception as e:
        print("❌ Error obteniendo archivo:", e)
        return None