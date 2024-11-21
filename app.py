
import os
import numpy as np
import cv2
import torch
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from flask import Flask, request, jsonify, Response
import json
from PIL import Image
from io import BytesIO
from requests_toolbelt.multipart.encoder import MultipartEncoder
import uuid
app = Flask(__name__)
@app.route('/extraer_cuadrados', methods=['POST'])
def extraer_cuadrados():
    '''s
    Preparación de los datos enviados por el usuario
    '''

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
   
    '''
    Preparamos el modelo
    '''

    HOME = os.getcwd()
    # Determinar el dispositivo basado en la variable de entorno
    device_type = os.getenv("DEVICE", "cpu")  # Por defecto 'cpu'
    DEVICE= torch.device("cuda" if device_type == "gpu" and torch.cuda.is_available() else "cpu")
    CONFIG= "sam2_hiera_l.yaml"
    CHECKPOINT=f"{HOME}/checkpoints/sam2_hiera_large.pt"
    app.logger.info(f"Usando dispositivo: {DEVICE}")
    sam2_model = build_sam2(CONFIG, CHECKPOINT, device=DEVICE, apply_postprocessing=False)
    predictor = SAM2ImagePredictor(sam2_model, device=DEVICE)
    
    
    try:
        img = Image.open(BytesIO(imagen))
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al procesar la imagen"}), 400
    
    image_bgr=np.array(img)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)

    masks, scores, logits = predictor.predict(
    box=boxes,
    multimask_output=False
    )
    if boxes.shape[0] != 1:
        masks = np.squeeze(masks)

    #Recortar y guardar las máscaras
    partes_form_data=[]
    for i, (mask, box) in enumerate(zip(masks, boxes)):
        try:
            app.logger.debug(f"Procesando máscara {i}, box: {box}")
            puntox1, puntoy1, puntox2, puntoy2 = box.astype(int)
            
            app.logger.debug(f"Coordenadas convertidas: {puntox1, puntoy1, puntox2, puntoy2}")
            
            # Comprobación de límites
            if puntox1 < 0 or puntoy1 < 0 or puntox2 > img.width or puntoy2 > img.height:
                raise ValueError(f"Las coordenadas están fuera de los límites de la imagen: {box}")
            
            recorte = img.crop((puntox1, puntoy1, puntox2, puntoy2))
            
            app.logger.debug(f"Tamaño del recorte: {recorte.size}")
            
             # Verificación de dimensiones de la máscara
            app.logger.debug(f"Dimensiones de la máscara: {mask.shape}")
            
            # Verificación de dimensiones de la máscara generada por el modelo
            ancho_recorte, alto_recorte = recorte.size  # Obtener dimensiones correctamente
            app.logger.debug(f"Tamaño del recorte: {recorte.size}")
            app.logger.debug(f"Dimensiones esperadas del recorte: {(alto_recorte, ancho_recorte)}")
            app.logger.debug(f"Dimensiones de la máscara: {mask.shape}")
            
            if mask.shape[0] != alto_recorte or mask.shape[1] != ancho_recorte:
                app.logger.debug("Redimensionando la máscara al tamaño del recorte")
                try:
                    mask_resized = cv2.resize(mask, (ancho_recorte, alto_recorte), interpolation=cv2.INTER_NEAREST)
                except Exception as resize_error:
                    raise ValueError(f"Error al redimensionar la máscara: {resize_error}")
            else:
                mask_resized = mask
            
            # Convertir el recorte a un array de NumPy para aplicar la máscara
            recorte_np = np.array(recorte.convert("RGB"), dtype=np.uint8)
        
            # Asegurarse de que la máscara tiene la misma forma que el recorte
            if mask_resized.shape[:2] != recorte_np.shape[:2]:
                raise ValueError(f"Las dimensiones de la máscara ({mask.shape}) no coinciden con el recorte ({recorte_np.shape})")
            
            # Aplicar la máscara al recorte
            recorte_np[mask_resized == 0] = 0  # Establecer los píxeles fuera de la máscara a negro
            recorte_final = Image.fromarray(recorte_np)
            # Guardar el recorte
            img_io = BytesIO()
            formato_salida = "JPEG" if mimetype == "image/jpeg" else "PNG"
            recorte_final.save(img_io, format=formato_salida)
            img_io.seek(0)
            partes_form_data.append(("mask_{}".format(i), (f"mask_{i}.png", img_io, mimetype)))
            app.logger.debug(f"Máscara {i} procesada y guardada exitosamente")
        except Exception as e:
            app.logger.error(f"Error al recortar o procesar la máscara {i}: {str(e)}")
            return jsonify({
                "status": "error", 
                "message": f"Error al recortar o procesar la máscara {i}",
                "details": str(e)  # Incluye detalles del error
            }), 400
    '''
    Calculamos el cuadrado grande
    '''
    
    min_col1 = np.min(boxes[:, 0])  # Mínimo de la primera columna
    min_col2 = np.min(boxes[:, 1])  # Mínimo de la segunda columna
    max_col3 = np.max(boxes[:, 2])  # Máximo de la tercera columna
    max_col4 = np.max(boxes[:, 3])  # Máximo de la cuarta columna
    cuadrado_grande = np.array([min_col1, min_col2, max_col3, max_col4])

    # Recortar la imagen al cuadrado grande
    try:
        x1, y1, x2, y2 = cuadrado_grande.astype(int)
        recorte_grande = img.crop((x1, y1, x2, y2))
        img_io_grande = BytesIO()
        formato_salida = "JPEG" if mimetype == "image/jpeg" else "PNG"
        nombre_salida = "cuadrado_grande.jpg" if formato_salida == "JPEG" else "cuadrado_grande.png"
        recorte_grande.save(img_io_grande, format=formato_salida)  # Usar el mismo formato que el original
        img_io_grande.seek(0)
        # Agregar al form-data con el nombre y tipo MIME correctos
        partes_form_data.append(("cuadrado_grande", (nombre_salida, img_io_grande, mimetype)))
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al recortar el cuadrado grande"}), 400

    # Retornar la imagen recortada
    cuerpo = MultipartEncoder(fields={
        nombre: (nombre_archivo, contenido, mimetype)
        for nombre, (nombre_archivo, contenido, mimetype) in partes_form_data
    })

    respuesta = Response(cuerpo.to_string(), content_type=cuerpo.content_type)
    return respuesta
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
