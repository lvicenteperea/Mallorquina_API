partes = "() () (1,2,3)".split(") (")
parte3 = partes[2].strip("()")
lista3_str = [item.strip().strip('"') for item in parte3.split(";")]
print(lista3_str)

lista3_str = [item.strip() for item in parte3.split(";")]
print(lista3_str)




# def separar_cadena(cadena):
#     """
#     Recibe una cadena con dos partes entre paréntesis y devuelve dos listas:
#     - Una con los elementos de la primera parte.
#     - Otra con los elementos de la segunda parte.

#     :param cadena: Cadena en formato '(...) (...)'
#     :return: Dos listas, una para cada parte.
#     """
#     # Separar las dos partes
#     partes = cadena.split(") (")
#     if len(partes) != 2:
#         raise ValueError("La cadena debe contener dos partes separadas por ') ('.")
    
#     # Limpiar paréntesis iniciales y finales
#     parte1 = partes[0].strip("()")
#     parte2 = partes[1].strip("()")
    
#     # Convertir cada parte en listas separando por comas
#     lista1 = [item.strip().strip('"') for item in parte1.split(",")]
#     lista2 = [item.strip().strip('"') for item in parte2.split(",")]
    
#     return lista1, lista2




# cadena = '("stIdEnt", "Fecha", "[Serie Puesto Facturacion]", "[Factura Num]", "[Id Relacion]") ("{v1} >= \'{v2}\'", "{v1} >= CONVERT(DATETIME, \'{v2}\', 121) ", "{v1} >= \'{v2}\'", "{v1} >= {v2}", "{v1} >= {v2}")'

# # Llamar a la función
# lista1, lista2 = separar_cadena(cadena)

# # Mostrar resultados
# print("Lista 1:", lista1)
# print("Lista 2:", lista2)




# from cryptography.fernet import Fernet
# # Generar una nueva clave
# new_key = Fernet.generate_key()
# print(new_key.decode())  # Muestra la clave para configurarla como variable de entorno



# import secrets
# SECRET_KEY = secrets.token_hex(32)  # Genera una clave de 64 caracteres (32 bytes)
# print(SECRET_KEY)



# cadena = "Fecha, Hora_Cobro, Tiempo, Id_Salon, Id_Mesa, Comensales, Tarifa, Idioma, Id_Turno, Id_Camarero, Id_Cliente_Habitacion, Id_Apertura_Puesto_Cobro, Factura_Num, Iva_porc, Descuento_porc, Base, Descuento, Impuesto, Total, Propina, Serie_Puesto_Facturacion, Id_Relacion, Id_Relacion_Cocina, Recien_Abierta, Bk, Bk1, Nombre_Cajero, Anulada, Fusion, Base2, Descuento2, Iva2_porc, Impuesto2, Dcto_Manual, Importe_Impresion, Salida_Receta, IdCobro_Propina, Descripcion_Cobro_Propina, lVeces_Impreso, Edad, IdTipoCli, IdEvento, Factura_Num_Cliente, Cocina_Evento, Cocina_Pedido, bDetenerComandaCocina_Mesa, Cocina_Pedido_2, CM_Id_Reserva, CM_Id_Cliente, Id_Envio_GS, bEnviando, Id_Envio_Realizado, bNoCompCocina, stIdEnt, Origen_BBDD"
# elementos = len(cadena.split(","))
# print(elementos)
         


# cadena2 = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
# elementos = len(cadena2.split(","))
# print(elementos)


# cadena3 = "datetime.datetime(2018), None, datetime.datetime(2018), 1, 1, 2, 0, 0, 1, 5, 0, 534, 1, Decimal('10.00'), Decimal('0.00'), Decimal('1.550'), Decimal('0.000'), Decimal('0.150'), Decimal('1.700'), Decimal('0.000'), 'T1', 1, 13, False, False, False, 'DIRECCION', False, False, Decimal('0.000'), Decimal('0.000'), Decimal('0.00'), Decimal('0.000'), False, Decimal('1.700'), False, 0, '', 1, 0, 0, 0, 0, '', '', False, '', '', '', 0, False, 1, None, '0610220837274849', 13"
# elementos = len(cadena3.split(","))
# print(elementos)






# import os

# def listar_archivos(directorio):
#     # Lista para almacenar los resultados
#     lista_archivos = []
    
#     # Recorrer el directorio y sus subdirectorios
#     for ruta_directorio, subdirs, archivos in os.walk(directorio):
#         for archivo in archivos:
#             # Generar la ruta completa del archivo
#             ruta_completa = os.path.join(ruta_directorio, archivo)
#             # Agregar el archivo con su ruta relativa
#             lista_archivos.append(f"{archivo}: {ruta_completa}")
    
#     # Ordenar la lista según la ruta completa
#     lista_archivos.sort(key=lambda x: x.split(": ", 1)[1])
    
#     return lista_archivos

# # Directorio raíz
# directorio_base = r"D:\Nube\GitHub\Mallorquina_API"

# # Obtener la lista de archivos
# archivos = listar_archivos(directorio_base)

# # Guardar los resultados en un archivo de texto o imprimirlos
# with open("lista_archivos.txt", "w", encoding="utf-8") as f:
#     for archivo in archivos:
#         f.write(archivo + "\n")

# # Mensaje de éxito
# print("Lista de archivos generada en 'lista_archivos.txt'")

