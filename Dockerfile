FROM python:3.11

# 🔧 Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero requirements para aprovechar cache
COPY requirements.txt /app/requirements.txt

WORKDIR /app

# Crear entorno virtual dentro del contenedor
ENV VIRTUAL_ENV=/app/.venv_docker
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

# Instalar dependencias
RUN $VIRTUAL_ENV/bin/pip install --upgrade pip
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r /app/requirements.txt

# Ahora sí copiar el código completo
COPY . /app

# Puerto
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "chatbotintegracion.chatbotintegracion:app", "--host", "0.0.0.0", "--port", "8000"]
