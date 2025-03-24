import os
import urllib.parse
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import gridfs

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales de MongoDB desde variables de entorno
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")  # Nombre del proyecto por defecto
DB_HOST = os.getenv("DB_HOST", "clusterapi.nici0.mongodb.net")

# Verificar que las credenciales están definidas
if not DB_USER or not DB_PASSWORD:
    raise ValueError("Error: Las variables de entorno DB_USER o DB_PASSWORD no están definidas")

# Codificar credenciales para la URL
encoded_user = urllib.parse.quote(DB_USER)
encoded_password = urllib.parse.quote(DB_PASSWORD)

# Construcción de la URI de conexión segura
MONGO_URI = (
    f"mongodb+srv://{encoded_user}:{encoded_password}@{DB_HOST}/"
    f"{DB_NAME}?retryWrites=true&w=majority&appName={DB_NAME}"
)

# Conectar a MongoDB con Server API v1
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

db = client[DB_NAME]  # Conectar a la base de datos
fs = gridfs.GridFS(db)  # GridFS para almacenamiento de archivos
collection = db["conversaciones"]  # Colección para historiales de conversación

# Verificar conexión a MongoDB
try:
    client.admin.command("ping")
    print("Conexión exitosa a MongoDB!")
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")
    raise

def guardar_archivo(ruta_archivo, nombre_archivo):
    """Guarda un archivo en MongoDB GridFS"""
    try:
        with open(ruta_archivo, "rb") as archivo:
            archivo_id = fs.put(archivo, filename=nombre_archivo)
        print(f"Archivo {nombre_archivo} guardado con ID {archivo_id}")
        return archivo_id
    except Exception as e:
        print(f"Error al guardar archivo {nombre_archivo}: {e}")
        return None

def obtener_archivo(nombre_archivo):
    """Obtiene un archivo desde MongoDB GridFS"""
    try:
        archivo = fs.find_one({"filename": nombre_archivo})
        if archivo:
            return archivo.read()  # Devuelve el contenido del archivo
        print(f"Archivo {nombre_archivo} no encontrado en GridFS")
        return None
    except Exception as e:
        print(f"Error al obtener archivo {nombre_archivo}: {e}")
        return None