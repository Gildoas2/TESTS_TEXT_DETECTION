# Función Metasam extraer cuadrados


##Descripción**
Este endpoint recibe un formdata que admite una imagen junto con un conjunto de pares de puntos que representaran las caja de donde se quiere extraer el texto. Devuelve en multipart formdata la seleccion de cada caja más la sección completa de donde se ha extraido todo. Es decir, si se han seleccionado 


##Ejemplo de solicitud
'''
curl --location 'url' \
--form 'image=@"ruta_del_archivo"' \
--form 'points="[
    {\"x1\": 100, \"y1\": 200, \"x2\": 200, \"y2\": 800},
    {\"x1\": 500, \"y1\": 500, \"x2\": 550, \"y2\": 1000}
]"'
'''
##Ejemplo de respuesta
 '''
--3e1c6f192546404394bb11ae05f9c828
Content-Disposition: form-data; name="mask_0"; filename="mask_0.png"# Correspondiente mascara a la primera caja.
Content-Type: image/jpeg
(archivo en binario)
--3e1c6f192546404394bb11ae05f9c828
Content-Disposition: form-data; name="mask_1"; filename="mask_1.png"# Correspondiente mascara de la segunda caja.
Content-Type: image/jpeg
(archivo en binario)
--3e1c6f192546404394bb11ae05f9c828
Content-Disposition: form-data; name="cuadrado_grande"; filename="cuadrado_grande.jpg"#Recorte del cuadrado más pequeño que contiene ambas cajas.
Content-Type: image/jpeg
(archivo en binario)
--3e1c6f192546404394bb11ae05f9c828--
'''
