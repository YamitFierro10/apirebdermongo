import os
import urllib.parse
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import gridfs

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales desde variables de entorno
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_CLUSTER = os.getenv("DB_CLUSTER")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Codificar la contraseña en caso de caracteres especiales
encoded_password = urllib.parse.quote(DB_PASSWORD)

# Construcción de la URI de conexión
uri = f"mongodb+srv://{DB_USER}:{encoded_password}@{DB_CLUSTER}/?retryWrites=true&w=majority&appName=ClusterApi"

# Conectar a MongoDB con Server API v1 y TLS habilitado
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)

db = client[DB_NAME]
fs = gridfs.GridFS(db)
collection = db["conversaciones"]

# Verificar la conexión
try:
    client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB!")
except Exception as e:
    print(f"❌ Error al conectar a MongoDB: {e}")

def guardar_archivo(ruta_archivo, nombre_archivo):
    """Guarda un archivo en MongoDB GridFS"""
    try:
        with open(ruta_archivo, "rb") as archivo:
            archivo_id = fs.put(archivo, filename=nombre_archivo)
        print(f"✅ Archivo {nombre_archivo} guardado con ID {archivo_id}")
        return archivo_id
    except Exception as e:
        print(f"❌ Error al guardar archivo: {e}")
        return None

def obtener_archivo(nombre_archivo):
    """Obtiene un archivo desde MongoDB GridFS"""
    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        if archivo:
            return archivo.read()  # Devuelve el contenido del archivo
        print("⚠️ Archivo no encontrado")
        return None
    except Exception as e:
        print(f"❌ Error al obtener archivo: {e}")
        return None
