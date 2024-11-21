# Usa una imagen base de Python
FROM python:3.10-slim

# Establece variables de entorno
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza el sistema e instala dependencias básicas
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
    # Crea un directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias y luego instálalas
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 
# Establece el entorno de la variable que determina si se usa GPU o CPU
ARG DEVICE=cpu
ENV DEVICE ${DEVICE}
# Instalar PyTorch según la variable de entorno DEVICE (GPU o CPU)
RUN if [ "$DEVICE" = "gpu" ]; then \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118; \
    else \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; \
    fi

# Copia el repositorio ya clonado al contenedor (realiza el clon manualmente fuera del Dockerfile)
COPY segment-anything-2 /app/segment-anything-2

# Instala el repositorio en modo editable
WORKDIR /app/segment-anything-2
RUN pip install --no-cache-dir -e .

# Descarga el archivo preentrenado "sam2_hiera_large.pt"
RUN mkdir -p /app/checkpoints && \
    wget -q https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_large.pt -P /app/checkpoints

# Vuelve al directorio principal de trabajo
WORKDIR /app

# Copia el resto de la aplicación al contenedor
COPY . .

# Expone el puerto en el que corre la aplicación (5000 para Flask, 8000 para Django, por ejemplo)
EXPOSE 8080

# Define el comando para ejecutar la aplicación
CMD ["python3", "app.py"]