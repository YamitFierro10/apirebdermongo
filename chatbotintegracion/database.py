from pymongo import MongoClient
import gridfs
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client_db = MongoClient(MONGO_URI, tls=True, tlsCAFile=None).chatbot_db
#db = client[""]

# GridFS para almacenamiento de archivos
fs = gridfs.GridFS(client_db)

# Colección para historiales de conversación
collection = client_db["conversaciones"]

def guardar_archivo(ruta_archivo, nombre_archivo):
    """Guarda un archivo en MongoDB GridFS"""
    with open(ruta_archivo, "rb") as archivo:
        archivo_id = fs.put(archivo, filename=nombre_archivo)
    print(f"Archivo {nombre_archivo} guardado con ID {archivo_id}")
    return archivo_id

def obtener_archivo(nombre_archivo):
    """Obtiene un archivo desde MongoDB GridFS"""
    archivo = fs.find_one({"filename": nombre_archivo})
    if archivo:
        return archivo.read()  # Devuelve el contenido del archivo
    return None