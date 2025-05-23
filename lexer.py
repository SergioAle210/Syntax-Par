import pickle
import os
from regexpToAFD import manual_join


# Funciones auxiliares (puedes importarlas desde yalex_utils si ya las tienes definidas)
def custom_trim(s: str) -> str:
    start = 0
    while start < len(s) and s[start] in " \t\n\r":
        start += 1
    end = len(s) - 1
    while end >= start and s[end] in " \t\n\r":
        end -= 1
    result = ""
    if start <= end:
        for i in range(start, end + 1):
            result += s[i]
    return result


def custom_is_digit(c: str) -> bool:
    o = ord(c)
    return 48 <= o <= 57


def custom_all_digits(s: str) -> bool:
    for ch in s:
        if not custom_is_digit(ch):
            return False
    return True


def custom_to_int(s: str) -> int:
    value = 0
    for ch in s:
        value = value * 10 + (ord(ch) - 48)
    return value


def ascii_numbers_to_chars(s: str) -> str:
    """
    Si s está compuesta solo de dígitos y espacios, convierte cada número a su carácter ASCII.
    Caso contrario, retorna s sin cambios.
    """
    if s.replace(" ", "").isdigit():
        # Separa la cadena en números (usamos split para separar, ya que el requerimiento es sustituir join)
        parts = s.split()
        # Convertir cada número a su carácter correspondiente
        chars = []
        for num in parts:
            chars.append(chr(int(num)))
        # Unir los caracteres sin separador usando manual_join
        return manual_join(chars, "")
    return s


# Excepción para errores léxicos
class LexicalError(Exception):
    pass


def lex(input_text: str, dfa: dict) -> list:
    """
    Analiza léxicamente el texto de entrada usando un autómata finito determinista (AFD).
    Parámetros:
      - input_text: texto de entrada a analizar.
      - dfa: diccionario que representa el AFD a utilizar. Debe incluir "initial_state",
             "accepting_states", "transitions" y "token_actions".
    Retorna:
      - Lista de tokens reconocidos, donde cada token es una tupla (tipo, lexema).

    Esta versión convierte cada carácter (incluyendo dígitos y el punto) a su valor ASCII
    (usando str(ord(c))) para la búsqueda en la tabla de transiciones.
    Además, si se detecta un error léxico, se genera un token de error y se continúa el análisis.
    """
    tokens = []
    errors = []  # Para acumular errores léxicos
    i = 0
    n = len(input_text)
    token_actions = dfa.get("token_actions", {})

    while i < n:
        current_state = dfa["initial_state"]
        j = i
        last_accepting_state = None
        last_accepting_index = (
            i - 1
        )  # Se actualiza cuando se encuentra un estado aceptante

        # Se recorre la entrada caracter a caracter
        while j < n:
            symbol = str(ord(input_text[j]))
            key = (current_state, symbol)
            if key in dfa["transitions"]:
                current_state = dfa["transitions"][key]
                # Si el estado actual es de aceptación, actualizamos la última posición aceptada
                if current_state in dfa["accepting_states"]:
                    last_accepting_state = current_state
                    last_accepting_index = j
                j += 1
            else:
                # No existe transición para el símbolo actual, se termina el avance
                break

        # Si no se encontró ningún estado de aceptación, se reporta error
        if last_accepting_state is None:
            error_msg = (
                f"Error léxico en la posición {i}: no se pudo formar un token válido "
                f"para '{input_text[i]}'"
            )
            # print(error_msg)
            errors.append(error_msg)
            tokens.append(("Error léxico", input_text[i]))
            i += 1
            continue

        # Se extrae el lexema correspondiente al último índice de aceptación
        lexeme = input_text[i : last_accepting_index + 1]

        # Se obtiene el token asociado al estado de aceptación
        mapping = token_actions.get(last_accepting_state, {})

        def get_numeric_keys(d):
            keys = []
            for k in d.keys():
                if isinstance(k, int):
                    keys.append(k)
                elif isinstance(k, str) and custom_all_digits(k):
                    keys.append(custom_to_int(k))
            return keys

        if mapping:
            if "merged" in mapping:
                merged_mapping = mapping["merged"]
                numeric_keys = get_numeric_keys(merged_mapping)
                if numeric_keys:
                    min_key = min(numeric_keys)
                    token_type = merged_mapping.get(
                        min_key, merged_mapping.get(str(min_key), "ID")
                    )
                else:
                    token_type = list(merged_mapping.values())[0]
            else:
                numeric_keys = get_numeric_keys(mapping)
                if numeric_keys:
                    min_key = min(numeric_keys)
                    token_type = mapping.get(min_key, mapping.get(str(min_key), "ID"))
                else:
                    token_type = "ID"
        else:
            token_type = "ID"

        # Convertir los números a caracteres ASCII si es necesario
        token_type = ascii_numbers_to_chars(token_type)

        tokens.append((token_type, lexeme))
        # Se salta al final del lexema reconocido
        i = last_accepting_index + 1

    return tokens


def main():
    # Cargar el AFD minimizado desde lexer.pickle usando pickle
    with open("./lexers/lexer-4.pickle", "rb") as f:
        dfa = pickle.load(f)

    try:
        with open("./random_data/random_data_3.txt", "r", encoding="utf-8") as f:
            # with open("input.txt", "r", encoding="utf-8") as f:
            # En lugar de usar .strip(), usamos custom_trim
            input_text = custom_trim(f.read())
    except FileNotFoundError:
        input_text = "abc+def*(ghi)+ahdffd32*(abc+def)*abd"
        with open("input.txt", "w", encoding="utf-8") as f:
            f.write(input_text)

    # print("Texto de entrada:")
    # print(input_text)

    path = "./output_lexers/slr-4"

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    lexer_out_path = path + "/lexer_output_3.txt"

    try:
        token_list = lex(input_text, dfa)
        # En lugar de imprimir en consola, escribimos la salida en un archivo.
        with open(lexer_out_path, "w", encoding="utf-8") as out:
            for token in token_list:
                out.write("Token: " + token[0] + ", Lexema: '" + token[1] + "'\n")
    except LexicalError as e:
        with open(lexer_out_path, "w", encoding="utf-8") as out:
            out.write(str(e))


if __name__ == "__main__":
    main()
