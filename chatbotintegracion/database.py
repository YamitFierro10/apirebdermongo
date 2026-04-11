import os
import certifi
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 🔹 variable de entorno
MONGO_URI = os.getenv("MONGO_URI")

# 🔹 cliente global
client = None


# =========================
# 🔌 CONEXIÓN AUTO-RECONNECT
# =========================
def get_client():
    global client

    try:
        if client is None:
            print("🔌 Conectando a MongoDB...")
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            client.admin.command("ping")
            print("✅ MongoDB conectado")

        return client

    except Exception as e:
        print("❌ Error conectando MongoDB:", e)
        client = None
        return None


# =========================
# 📦 COLECCIÓN
# =========================
def get_collection():
    try:
        client = get_client()

        if client is None:
            return None

        db = client["chatbot_db"]
        return db["conversaciones"]

    except Exception as e:
        print("❌ Error obteniendo colección:", e)
        return None


# =========================
# 📁 GRIDFS
# =========================
def get_fs():
    try:
        client = get_client()

        if client is None:
            return None

        db = client["chatbot_db"]
        return gridfs.GridFS(db)

    except Exception as e:
        print("❌ Error GridFS:", e)
        return None


def guardar_archivo(ruta_archivo, nombre_archivo):
    fs = get_fs()

    if fs is None:
        return None

    try:
        with open(ruta_archivo, "rb") as archivo:
            file_id = fs.put(archivo, filename=nombre_archivo)

        print(f"📁 Archivo guardado: {nombre_archivo}")
        return file_id

    except Exception as e:
        print("❌ Error guardando archivo:", e)
        return None


def obtener_archivo(nombre_archivo):
    fs = get_fs()

    if fs is None:
        return None

    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        return archivo.read() if archivo else None

    except Exception as e:
        print("❌ Error obteniendo archivo:", e)
        return None