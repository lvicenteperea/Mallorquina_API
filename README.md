Sobre los servicios:
Estos siempre han de recibir 4 parametros, los cuatro primeros y por este orden:
    - id_App: Obligatorio, neceistamos saber que aplicación es la que está intentando acceder
    - user: si es una web que no tiene usuarios definidos o autenticados, indicar "NOMBRE_DE_LA_WEB"
    - ret_code: En principio debe llegar con cero o vacio, en el se retorna el código de error que la BBDD retorna
    - ret_txt: Texto que retorna la BBDD, en principio para el usuario.
    
Siempre retorna los valores "ret_*", que siempre actuan de la siguiente manera, dependiendo de RET_CODE:
    - ret_code = 0: El programa a terminado Ok
        - ret_txt: Texto que retorna la BBDD, en principio para el usuario. No suele hacer falta o es un simple OK
        - request: 2xx

    - ret_code > 0: El programa a terminado Ok, pero quiere indicar alguna particularidad, que se debe indicar en la documentación
        - ret_txt: Texto que retorna la BBDD, en principio para el usuario. No suele hacer falta o es un simple OK
        - Ejemplo: en un login:
            - Si es 0: Login correcto, entrar en el programa
            - Si es 1: Login correcto, pero contraseña va a caducar. Preguntar el usuario si quiere cambiar ya la contrasela porque le va a caducar
            - Si es 2: La contraseña ha caducado, debe cambiarla
            - Si es 3: Tiene que cambiar la contraseña por otros motivos.
        - request: 2xx

    - ret_code < 0:
        - ret_code = -99: Error del sistema. 
            - request: 5xx

        - ret_code entre -98 y -1: Lo mismo que en positivo pero serían errores de sistema. Lo normal es -1 y que ret_txt tenga el mensaje para el usuario. 
            - request: 4xx


Independientemente de esto, que es para control interno y manejo de mensajes, 

SEGURIDAD
1. Autenticación con JWT: Para que solo usuarios autorizados puedan acceder a tus APIs, tanto desde la web como desde servidores externos.
2. CORS: Para permitir solo llamadas desde dominios confiables (tu web).
3. Rate Limiting: Para prevenir abusos y ataques de fuerza bruta.
4. HTTPS: Obligatorio en producción para proteger la comunicación entre clientes y tu API.
5. Validación de entrada con Pydantic: Para garantizar que las solicitudes sean válidas y evitar inyecciones.

Tambien deberíamos crear un middleware personalizado y ver como mejoramos los logs