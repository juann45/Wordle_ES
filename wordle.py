import os
import sys
import random
import unicodedata
import urllib.request
import urllib.parse
import json

# Códigos de color ANSI para fondo
VERDE = '\033[42m'
AMARILLO = '\033[43m'
ROJO = '\033[41m'
RESET = '\033[0m'

def limpiar_pantalla():
    """Limpia la consola (Windows y Unix)."""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def pedir_entero(prompt, min_val, max_val):
    """
    Pide un número entero entre min_val y max_val (ambos inclusive).
    Sigue solicitando hasta recibir un valor válido.
    """
    while True:
        try:
            n = int(input(prompt))
            if min_val <= n <= max_val:
                return n
            else:
                print(f"Por favor, ingresa un número entre {min_val} y {max_val}.")
        except ValueError:
            print("Entrada inválida. Ingresa un número entero.")

def quitar_acentos(palabra: str) -> str:
    """
    Elimina acentos y eñes convirtiéndolos a sus equivalentes ASCII básicos,
    y devuelve la cadena en minúsculas sin diacríticos.
    """
    nfkd = unicodedata.normalize('NFKD', palabra)
    sin_diacriticos = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return sin_diacriticos.lower()

def obtener_palabras_de_internet(longitud: int) -> list[str]:
    """
    Consulta la API de Datamuse para obtener palabras en español de la longitud dada.
    Usa el patrón '?'*longitud para pedir todas las palabras de esa longitud.
    Retorna una lista de palabras sin acentos ni caracteres no alfabéticos.
    """
    patron = '?' * longitud
    query = urllib.parse.urlencode({
        'sp': patron,
        'v': 'es',
        'max': '1000'  # Límite máximo de resultados a solicitar
    })
    url = f"https://api.datamuse.com/words?{query}"

    try:
        with urllib.request.urlopen(url, timeout=10) as respuesta:
            raw = respuesta.read().decode('utf-8')
    except Exception as e:
        print(f"Error al conectarse a Datamuse: {e}")
        return []

    try:
        datos = json.loads(raw)
    except json.JSONDecodeError:
        print("No se pudo decodificar la respuesta JSON.")
        return []

    palabras = []
    for entry in datos:
        w = entry.get('word', '')
        # Normalizar y quitar diacríticos
        w_norm = quitar_acentos(w)
        # Verificar que tras normalizar siga teniendo la longitud exacta y solo letras
        if len(w_norm) == longitud and w_norm.isalpha():
            palabras.append(w_norm)

    # Eliminar duplicados
    return list(dict.fromkeys(palabras))

def validar_intento(intento: str, longitud: int) -> bool:
    """
    Verifica que el intento tenga la longitud correcta y solo contenga letras a–z.
    """
    return len(intento) == longitud and intento.isalpha()

def evaluar_intento(intento: str, secreto: str) -> list[tuple[str, str]]:
    """
    Dado un intento y la palabra secreta, devuelve una lista de tuplas:
      (letra, código_color_ANSI)
    donde:
      - VERDE:   letra en posición correcta
      - AMARILLO: letra existe en otra posición
      - ROJO:    letra no está en la palabra secreta

    Primero marca verdes, luego cuenta las letras restantes del secreto
    para determinar amarillos correctamente.
    """
    n = len(secreto)
    resultado = [("", "")] * n
    usado_en_secreto = [False] * n  # posiciones ya marcadas verde

    # 1) Primera pasada: marcaremos VERDE para coincidencias exactas
    for i in range(n):
        if intento[i] == secreto[i]:
            resultado[i] = (intento[i], VERDE)
            usado_en_secreto[i] = True

    # 2) Contar cuántas veces aparece cada letra "no verde" en el secreto
    conteo_resto = {}
    for i in range(n):
        if not usado_en_secreto[i]:
            letra = secreto[i]
            conteo_resto[letra] = conteo_resto.get(letra, 0) + 1

    # 3) Segunda pasada: para las letras que no son verdes, vemos si caben como amarillas
    for i in range(n):
        if resultado[i][1] == "":  # aún no marcado
            letra = intento[i]
            if conteo_resto.get(letra, 0) > 0:
                resultado[i] = (letra, AMARILLO)
                conteo_resto[letra] -= 1
            else:
                resultado[i] = (letra, ROJO)

    return resultado

def mostrar_tablero(intentos_info: list[list[tuple[str, str]]]):
    """
    Imprime en consola cada intento coloreando cada letra según la evaluación.
    """
    for evaluacion in intentos_info:
        linea = ""
        for letra, color in evaluacion:
            linea += f"{color} {letra.upper()} {RESET} "
        print(linea)
    print()  # línea en blanco al final

def jugar_wordle_es():
    limpiar_pantalla()
    print("=== BIENVENIDO A WORDLE-ES (Python con API Datamuse) ===\n"
          "Adivina la palabra secreta en el número de intentos que elijas.\n"
          "El programa obtendrá palabras en español desde Datamuse:\n"
          "Verde = letra en posición correcta | Amarillo = letra en palabra pero en otra posición | Rojo = letra no está.\n")

    # 1) Pedir longitud (5 a 10)
    longitud = pedir_entero("¿Cuántas letras tendrá la palabra? (5–10): ", 5, 10)

    # 2) Pedir número de intentos
    max_intentos = pedir_entero("¿Cuántos intentos deseas tener? (1–20): ", 1, 20)

    # 3) Descargar lista de palabras desde Datamuse y filtrar
    print(f"\nObteniendo palabras de {longitud} letras desde Datamuse...")
    lista_palabras = obtener_palabras_de_internet(longitud)
    if not lista_palabras:
        print(f"No se encontraron palabras de {longitud} letras o hubo un error de conexión.")
        sys.exit(1)

    secreto = random.choice(lista_palabras)
    # Para depuración, podrías imprimir: print(f"[DEBUG] Secreto: {secreto}")

    limpiar_pantalla()
    print(f"¡Comienza el juego! Tienes {max_intentos} intentos para adivinar una palabra de {longitud} letras.\n")

    intentos_info = []
    intentos_hechos = 0

    while intentos_hechos < max_intentos:
        intento = input(f"Intento {intentos_hechos + 1}/{max_intentos} - Ingresa tu palabra: ").strip().lower()
        intento = quitar_acentos(intento)

        if not validar_intento(intento, longitud):
            print(f"La palabra debe tener exactamente {longitud} letras y solo caracteres alfabéticos.\n")
            continue

        evaluacion = evaluar_intento(intento, secreto)
        intentos_info.append(evaluacion)
        intentos_hechos += 1

        limpiar_pantalla()
        print(f"Intentos: {intentos_hechos}/{max_intentos}\n")
        mostrar_tablero(intentos_info)

        # Verificar si ganó (todas las letras en verde)
        if all(color == VERDE for (_, color) in evaluacion):
            print("🎉 ¡FELICIDADES! ¡Adivinaste la palabra correctamente! 🎉\n")
            break
        else:
            if intentos_hechos < max_intentos:
                print("Sigue intentando...\n")
            else:
                print("Se acabaron los intentos.")
                print(f"La palabra secreta era: {secreto.upper()}\n")

    print("Gracias por jugar a Wordle-ES.")

if __name__ == "__main__":
    try:
        jugar_wordle_es()
    except KeyboardInterrupt:
        print("\nJuego interrumpido. ¡Hasta la próxima!")
        sys.exit(0)
