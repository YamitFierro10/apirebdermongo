FROM python:3.11

COPY . /app
WORKDIR /app

# Crear y activar el entorno virtual
ENV VIRTUAL_ENV=/app/.venv_docker
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV  # Crea el entorno virtual

# Instalar dependencias dentro del entorno virtual
RUN $VIRTUAL_ENV/bin/pip install --upgrade pip
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que correrá FastAPI
EXPOSE 8000

# Comando de inicio para FastAPI
CMD ["uvicorn", "chatbotintegracion.chatbotintegracion:app", "--host", "0.0.0.0", "--port", "8000"]
