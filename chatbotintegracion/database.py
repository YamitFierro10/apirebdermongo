import os
import certifi
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 🔥 variables
MONGO_URI = os.getenv("MONGO_URI")

# 🔹 cliente global (se reconecta solo)
client = None


# =========================
# 🔌 CONEXIÓN PRO (AUTO-RECONNECT)
# =========================

def get_client():
    """
    Retorna cliente Mongo activo o crea uno nuevo
    """
    global client

    try:
        if client is None:
            print("🔌 Conectando a MongoDB...")
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            client.admin.command("ping")
            print("✅ MongoDB conectado correctamente")

        return client

    except Exception as e:
        print("❌ Error conectando MongoDB:", e)
        client = None
        return None


def get_collection():
    """
    Obtiene la colección de conversaciones (SIEMPRE intenta reconectar)
    """
    try:
        client = get_client()

        if client is None:
            print("❌ No hay cliente Mongo")
            return None

        db = client["chatbot_db"]
        collection = db["conversaciones"]

        return collection

    except Exception as e:
        print("❌ Error obteniendo colección:", e)
        return None


def get_fs():
    """
    Obtiene GridFS (auto-reconecta)
    """
    try:
        client = get_client()

        if client is None:
            print("❌ No hay cliente Mongo para GridFS")
            return None

        db = client["chatbot_db"]
        return gridfs.GridFS(db)

    except Exception as e:
        print("❌ Error obteniendo GridFS:", e)
        return None


# =========================
# 📁 GRIDFS FUNCTIONS
# =========================

def guardar_archivo(ruta_archivo, nombre_archivo):
    """Guarda archivo en MongoDB GridFS"""
    fs = get_fs()

    if fs is None:
        print("❌ GridFS no disponible")
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
    fs = get_fs()

    if fs is None:
        print("❌ GridFS no disponible")
        return None

    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        return archivo.read() if archivo else None

    except Exception as e:
        print("❌ Error obteniendo archivo:", e)
        return None