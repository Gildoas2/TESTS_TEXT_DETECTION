# Usa una imagen base de Python
FROM python:3.10.12

# Crea un directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias y luego instálalas
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el resto de la aplicación al contenedor
COPY . .

# Expone el puerto en el que corre la aplicación (5000 para Flask, 8000 para Django, por ejemplo)
EXPOSE 5000

# Define el comando para ejecutar la aplicación
CMD ["python", "app.py"]
