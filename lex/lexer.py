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

def lex(input_text: str, dfa: dict):
    """
    Función léxica que convierte una cadena de entrada en una secuencia de tokens usando un AFD.
    Devuelve tuplas (token_type, lexeme), donde token_type es el nombre simbólico (ej. 'PLUS').
    """
    i = 0
    n = len(input_text)
    token_actions = dfa.get("token_actions", {})

    while i < n:
        current_state = dfa["initial_state"]
        j = i
        last_accepting_state = None
        last_accepting_index = i - 1

        while j < n:
            symbol = str(ord(input_text[j]))
            key = (current_state, symbol)
            if key in dfa["transitions"]:
                current_state = dfa["transitions"][key]
                if current_state in dfa["accepting_states"]:
                    last_accepting_state = current_state
                    last_accepting_index = j
                j += 1
            else:
                break

        if last_accepting_state is None:
            yield ("Error léxico", input_text[i])
            i += 1
            continue

        lexeme = input_text[i : last_accepting_index + 1]
        mapping = token_actions.get(last_accepting_state, {})
        token_type = "ID"  # valor por defecto

        if "merged" in mapping:
            merged_mapping = mapping["merged"]
            numeric_keys = []
            for k in merged_mapping.keys():
                if isinstance(k, int):
                    numeric_keys.append(k)
                elif isinstance(k, str) and k.isdigit():
                    numeric_keys.append(int(k))
            if numeric_keys:
                min_key = min(numeric_keys)
                token_type = merged_mapping.get(min_key, merged_mapping.get(str(min_key), "ID"))
            else:
                token_type = list(merged_mapping.values())[0]
        else:
            numeric_keys = []
            for k in mapping.keys():
                if isinstance(k, int):
                    numeric_keys.append(k)
                elif isinstance(k, str) and k.isdigit():
                    numeric_keys.append(int(k))
            if numeric_keys:
                min_key = min(numeric_keys)
                token_type = mapping.get(min_key, mapping.get(str(min_key), "ID"))
            else:
                token_type = "ID"

        # Asegurar que cualquier token codificado como ASCII se traduzca
        token_type = ascii_numbers_to_chars(token_type)

        yield (token_type, lexeme)
        i = last_accepting_index + 1





def main():
    # Cargar el AFD minimizado desde lexer.pickle usando pickle
    with open("../lexers/lexer-test.pickle", "rb") as f:
        dfa = pickle.load(f)

    try:
        with open("../tests/test_num.txt", "r", encoding="utf-8") as f:
            # with open("input.txt", "r", encoding="utf-8") as f:
            # En lugar de usar .strip(), usamos custom_trim
            input_text = custom_trim(f.read())
    except FileNotFoundError:
        input_text = "abc+def*(ghi)+ahdffd32*(abc+def)*abd"
        with open("input.txt", "w", encoding="utf-8") as f:
            f.write(input_text)

    # print("Texto de entrada:")
    # print(input_text)

    path = "../output_lexers/slr-"

    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    lexer_out_path = path + "/lexer_output_test1.txt"

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
