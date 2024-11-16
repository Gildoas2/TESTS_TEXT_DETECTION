import os
import numpy as np
from flask import Flask, request, jsonify, send_file
import json
from PIL import Image
from io import BytesIO
app = Flask(__name__)
@app.route('/extraer_cuadrados', methods=['POST'])
def extraer_cuadrados(request):

    # Verificar si se envió una imagen
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "La imagen es requerida"}), 400
    archivo_imagen=request.files['image']
    if not archivo_imagen:
        return jsonify({"status": "error", "message": "No se encontró la imagen"}), 400
    
    #Detectar el formato de la imagen
    mimetype = archivo_imagen.mimetype
    if mimetype not in ['image/jpeg', 'image/png']:
        return jsonify({"status": "error", "message": "Formato de imagen no soportado"}), 400
    
    # Leer la imagen como binario
    imagen=archivo_imagen.read()

    #Extraemos los cuadrados
    puntos=request.form.get('points')
    if not puntos:
         return jsonify({"status": "error", "message": "No se encontraron puntos"}), 400
    
    # Convertir la cadena JSON a una lista de diccionarios
    try:
        puntos = json.loads(puntos)  # Convierte el JSON en una lista de diccionarios
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Error al decodificar los puntos JSON"}), 400
    
    # Convertir los puntos en un array de cuadros delimitadores
    try:
        boxes = np.array([
            [box['x1'], box['y1'], box['x2'], box['y2']]
            for box in puntos
        ])
    except KeyError:
        return jsonify({"status": "error", "message": "Formato de puntos incorrecto"}), 400
    #Calculamos el cuadrado grande
    min_col1 = np.min(boxes[:, 0])  # Mínimo de la primera columna
    min_col2 = np.min(boxes[:, 1])  # Mínimo de la segunda columna
    max_col3 = np.max(boxes[:, 2])  # Máximo de la tercera columna
    max_col4 = np.max(boxes[:, 3])  # Máximo de la cuarta columna
    cuadrado_grande = np.array([min_col1, min_col2, max_col3, max_col4])

    # Abrir la imagen original usando Pillow
    try:
        img = Image.open(BytesIO(imagen))
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al procesar la imagen"}), 400

    # Recortar la imagen al cuadrado grande
    try:
        x1, y1, x2, y2 = cuadrado_grande.astype(int)
        recorte = img.crop((x1, y1, x2, y2))
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al recortar la imagen"}), 400

    # Convertir la imagen recortada a bytes para enviarla
    img_io = BytesIO()
    formato_salida = "JPEG" if mimetype == "image/jpeg" else "PNG"
    recorte.save(img_io, format=formato_salida)  # Usar el mismo formato que el original
    img_io.seek(0)

    # Retornar la imagen recortada
    mimetype_respuesta = "image/jpeg" if formato_salida == "JPEG" else "image/png"
    return send_file(img_io, mimetype=mimetype_respuesta)