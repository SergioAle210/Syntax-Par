import pickle
import os


# ────── helpers reutilizados ──────
def manual_join(strings: list, sep: str) -> str:
    res = ""
    for i in range(len(strings)):
        if i:
            res += sep
        res += strings[i]
    return res


def custom_trim(s: str) -> str:
    i, j = 0, len(s) - 1
    while i <= j and s[i] in " \t\n\r":
        i += 1
    while j >= i and s[j] in " \t\n\r":
        j -= 1
    out = ""
    while i <= j:
        out += s[i]
        i += 1
    return out


# ────── conversión de "59" → ";" ──────
def code_to_char(code: str) -> str:
    """
    • '59'   → ';'
    • 'ws'   → 'ws'
    • 'id'   → 'id'
    • ''     → ''
    """
    if code.isdigit():
        try:
            return chr(int(code))
        except ValueError:
            pass
    return code


# ────── excepción propia ──────
class LexicalError(Exception):
    pass


# ────── motor léxico ──────
def lex(text: str, dfa: dict):
    """
    Genera tuplas ((símbolo_convertido, TOKEN), lexema)
    por ejemplo: ((';', 'SEMICOLON'), ';')
    """
    i, n = 0, len(text)
    trans = dfa["transitions"]
    acc = set(dfa["accepting_states"])
    token_actions = dfa["token_actions"]
    initial = dfa["initial_state"]

    while i < n:
        state = initial
        j = i
        last_state = None
        last_j = i - 1

        # ── recorrer el AFD ──
        while j < n:
            sym = str(ord(text[j]))
            key = (state, sym)
            if key in trans:
                state = trans[key]
                if state in acc:
                    last_state = state
                    last_j = j
                j += 1
            else:
                break

        # ── si no cayó en aceptación ──
        if last_state is None:
            yield (("ERROR", "LEXICAL"), text[i])
            i += 1
            continue

        lexeme = text[i : last_j + 1]
        mapping = token_actions.get(last_state, {})

        # ── resolver la tupla (symCode, TOKEN) con prioridad a menor marcador ──
        def pick(mapping_dict):
            # mapping_dict: id → (symCode, TOKEN)
            int_keys = [int(k) for k in mapping_dict.keys()]
            min_id = min(int_keys)
            tup = mapping_dict.get(min_id) or mapping_dict.get(str(min_id))
            return tup

        if isinstance(mapping, dict) and "merged" in mapping:
            tup = pick(mapping["merged"])
        else:
            tup = pick(mapping)

        # fallback seguro
        if tup is None:
            tup = ("", "ID")

        sym_code, token_name = tup
        symbol_conv = code_to_char(sym_code)

        yield ((symbol_conv, token_name), lexeme)
        i = last_j + 1


# ────── pequeño CLI / prueba ──────
def main():
    # carga del AFD minimizado
    with open("../lexers/lexer-1.pickle", "rb") as f:
        dfa = pickle.load(f)

    # texto de entrada
    try:
        with open("../tests/test.txt", encoding="utf-8") as f:
            input_text = custom_trim(f.read())
    except FileNotFoundError:
        input_text = "a + b * (c);"

    # carpeta de salida
    out_dir = "../output_lexers/slr-1"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lexer_output_test1.txt")

    # ejecutar lexer y guardar resultado
    with open(out_path, "w", encoding="utf-8") as out:
        for token, lexeme in lex(input_text, dfa):
            out.write(f"Token: {token}, Lexema: '{lexeme}'\n")


if __name__ == "__main__":
    main()
