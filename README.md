 


Sobre los servicios:
Estos siempre han de recibir 4 parametros, los cuatro primeros y por este orden:
    - id_App: Obligatorio, neceistamos saber que aplicación es la que está intentando acceder
    - user: si es una web que no tiene usuarios definidos o autenticados, indicar "NOMBRE_DE_LA_WEB"
    - ret_code: En principio debe llegar con cero o vacio, en el se retorna el código de error que la BBDD retorna
    - ret_txt: Texto que retorna la BBDD, en principio para el usuario.
    
Siempre retorna los valores "ret_*", que siempre actuan de la siguiente manera, dependiendo de RET_CODE:
    - ret_code = 0: El programa a terminado Ok
        - ret_txt: Texto que retorna la BBDD, en principio para el usuario. No suele hacer falta o es un simple OK

    - ret_code > 0: El programa a terminado Ok, pero quiere indicar alguna particularidad, que se debe indicar en la documentación
        - ret_txt: Texto que retorna la BBDD, en principio para el usuario. No suele hacer falta o es un simple OK
        - Ejemplo: en un login:
            - Si es 0: Login correcto, entrar en el programa
            - Si es 1: Login correcto, pero contraseña va a caducar. Preguntar el usuario si quiere cambiar ya la contrasela porque le va a caducar
            - Si es 2: La contraseña ha caducado, debe cambiarla
            - Si es 3: Tiene que cambiar la contraseña por otros motivos.
    - ret_code < 0: Lo mismo que en positivo pero serían errores de sistema. Lo normal es -1 y que ret_txt tenga el mensaje para el usuario
