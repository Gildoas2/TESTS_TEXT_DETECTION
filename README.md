# Función Metasam extraer cuadrados


##Descripción**
Este endpoint recibe una imagen junto con un conjunto de pares de puntos. Se devolverá la zona seleccionada y los cuadrados delimitados por los pares de puntos (Siendo estos el superior-izquierdo y el inferior-derecho).

##Estructura de la solicitud
La solicitud debe ser un objeto JSON que contenga los siguientes campos:
+ `image` (requerido, tipo:`string`)
    + Una cadena en Base64 que representa la imagen en jpg o png
+ `points` (requerido, tipo:`array`)
    + Una lista de objetos, cada uno contiene un par de puntos con coordenadas.
    + Cada objeto dentro del array debe tener:
        +`x1` (requerido, tipo: `number`): Coordenada X del primer punto.
        +`y1` (requerido, tipo: `number`): Coordenada Y del primer punto.
        +`x2` (requerido, tipo: `number`): Coordenada X del segundo punto.
        +`y2` (requerido, tipo: `number`): Coordenada Y del segundo punto.

##Ejemplo de solicitud
'''
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "points": [
    {"x1": 100, "y1": 150, "x2": 200, "y2": 250},
    {"x1": 300, "y1": 350, "x2": 400, "y2": 450},
    {"x1": 50, "y1": 75, "x2": 125, "y2": 175}
  ]
}
'''
