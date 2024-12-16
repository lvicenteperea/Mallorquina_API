

def imprime(textos: list, relleno: str = "", modo: int = 1):
    """
    Función que imprime textos con líneas de relleno al inicio y al final.

    Parámetros:
    - textos: lista de textos a imprimir.
    - relleno: carácter que se repetirá en la línea de relleno.
    - modo: 1 (por defecto) imprime todos los textos en la misma línea;
            otro valor imprime cada texto en una línea distinta.
    """
    # Determinar el ancho de las líneas de relleno
    if relleno and relleno.strip() != "":
        ancho = max(len(str(texto)) for texto in textos) + 10  # Añade un extra para que se vea mejor
        linea_relleno = relleno * ancho
 
         # Imprimir la línea de relleno al inicio
        print(linea_relleno)

    # Imprimir los textos
    if modo == 1:
        # print(" ".join(textos))  # Todos los textos en la misma línea
        resultado = "<" + "> - <".join(str(elemento) for elemento in textos) + ">"
        print(resultado)
    else:
        for texto in textos:  # Cada texto en una línea separada
            print(texto)

    if relleno:
        # Imprimir la línea de relleno al final
        print(linea_relleno)
