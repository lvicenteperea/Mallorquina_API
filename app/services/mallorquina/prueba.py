# from cryptography.fernet import Fernet
# # Generar una nueva clave
# new_key = Fernet.generate_key()
# print(new_key.decode())  # Muestra la clave para configurarla como variable de entorno



# import secrets
# SECRET_KEY = secrets.token_hex(32)  # Genera una clave de 64 caracteres (32 bytes)
# print(SECRET_KEY)




import os

def listar_archivos(directorio):
    # Lista para almacenar los resultados
    lista_archivos = []
    
    # Recorrer el directorio y sus subdirectorios
    for ruta_directorio, subdirs, archivos in os.walk(directorio):
        for archivo in archivos:
            # Generar la ruta completa del archivo
            ruta_completa = os.path.join(ruta_directorio, archivo)
            # Agregar el archivo con su ruta relativa
            lista_archivos.append(f"{archivo}: {ruta_completa}")
    
    # Ordenar la lista según la ruta completa
    lista_archivos.sort(key=lambda x: x.split(": ", 1)[1])
    
    return lista_archivos

# Directorio raíz
directorio_base = r"D:\Nube\GitHub\Mallorquina_API"

# Obtener la lista de archivos
archivos = listar_archivos(directorio_base)

# Guardar los resultados en un archivo de texto o imprimirlos
with open("lista_archivos.txt", "w", encoding="utf-8") as f:
    for archivo in archivos:
        f.write(archivo + "\n")

# Mensaje de éxito
print("Lista de archivos generada en 'lista_archivos.txt'")