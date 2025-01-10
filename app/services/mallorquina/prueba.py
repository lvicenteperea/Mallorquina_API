from cryptography.fernet import Fernet

# Generar una nueva clave
new_key = Fernet.generate_key()
print(new_key.decode())  # Muestra la clave para configurarla como variable de entorno
