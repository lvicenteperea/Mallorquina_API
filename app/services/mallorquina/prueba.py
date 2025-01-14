# from cryptography.fernet import Fernet

# # Generar una nueva clave
# new_key = Fernet.generate_key()
# print(new_key.decode())  # Muestra la clave para configurarla como variable de entorno



import secrets

SECRET_KEY = secrets.token_hex(32)  # Genera una clave de 64 caracteres (32 bytes)
print(SECRET_KEY)