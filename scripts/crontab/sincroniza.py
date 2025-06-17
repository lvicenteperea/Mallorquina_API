#!/usr/bin/env python3

"""
# Esto es un fichero para ejecutar directamente desde el SO, por eso la primera línea es "#!/usr/bin/env python3", para eso hay que darle premisos:
#       chmod +x sincroniza.py
#
# Luego en el crontab poner algo parecido a esto:
#       0 3 * * * python scripts\crontab\sincroniza.py --id_app 1 --user "Crontab"  >> logs\Sincroniza.log 2>&1
#
# En Vindows:
#       python sincroniza.py --id_app 1 --user "Crontab"
"""
import argparse

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.utils.InfoTransaccion import InfoTransaccion
from app.services.mallorquina import sincroniza

def main():
    parser = argparse.ArgumentParser(
        description='Ejecuta el proceso de sincronización real con parámetros desde terminal.'
    )
    parser.add_argument('--id_app', type=int, default=0, help='ID de la aplicación')
    parser.add_argument('--user', type=str, default='Sistema_', help='Usuario del sistema que ejecuta')
    # parser.add_argument('--parametros', nargs='+', help='Lista de parámetros principales (ej:  NO_HAY1  NO_HAY2)', required=True)

    args = parser.parse_args()

    # Prepara el objeto InfoTransaccion
    info = InfoTransaccion(
        id_App=args.id_app,
        user=args.user
        # ,parametros=[args.parametros]
    )

    # Llama a la función REAL de sincronización
    resultado = sincroniza.proceso(info)

    print("\n------ RESULTADO FINAL ------")
    print("Resultado:", resultado)

if __name__ == '__main__':
    main()
