import os
import certifi
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = None
client_db = None
collection = None
fs = None


# =========================
# 🔥 CONEXIÓN
# =========================
def conectar_db():
    global client, client_db, collection, fs

    if client is not None:
        return

    MONGO_URI = os.getenv("MONGO_URI")

    try:
        print("🔌 Conectando a MongoDB...")
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        client.admin.command("ping")

        client_db = client["chatbot_db"]
        collection = client_db["conversaciones"]
        fs = gridfs.GridFS(client_db)

        print("✅ MongoDB conectado correctamente")

    except Exception as e:
        print("❌ Error conectando MongoDB:", e)
        client = None


# =========================
# 📦 GET COLLECTION
# =========================
def get_collection():
    global collection

    if collection is None:
        conectar_db()

    return collection


# =========================
# 🧠 HISTORIAL
# =========================
def obtener_historial(usuario, limite=10):
    col = get_collection()

    if col is None:
        return []

    try:
        mensajes = list(
            col.find({"usuario": usuario})
            .sort("timestamp", -1)
            .limit(limite)
        )

        mensajes.reverse()
        return mensajes

    except Exception as e:
        print("❌ Error obteniendo historial:", e)
        return []


# =========================
# 📁 GRIDFS
# =========================
def guardar_archivo(ruta_archivo, nombre_archivo):
    if fs is None:
        conectar_db()

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
    if fs is None:
        conectar_db()

    if fs is None:
        return None

    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        return archivo.read() if archivo else None

    except Exception as e:
        print("❌ Error obteniendo archivo:", e)
        return None