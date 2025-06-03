import os
import pickle
import sys
from LR0 import Grammar, lr0_items, visualize_lr0_automaton
from first_follow import compute_first, compute_follow
from SLR import enumerate_productions, save_slr_table, compute_slr_table
from sim_slr import simulate_slr_parser

# --- IMPORTAR EL LEXER ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../lex")))
from lexer import lex  # noqa: E402 (import tardío intencional)


def str_startswith(cadena: str, prefijo: str) -> bool:
    """Equivalente a str.startswith."""
    if len(prefijo) > len(cadena):
        return False
    for i in range(len(prefijo)):
        if cadena[i] != prefijo[i]:
            return False
    return True


def trim(cadena: str) -> str:
    """Recorta espacios y tabulaciones al inicio y fin (equiv. a str.strip)."""
    izquierda = 0
    derecha = len(cadena) - 1
    while izquierda <= derecha and cadena[izquierda] in (" ", "\t", "\n", "\r"):
        izquierda += 1
    while derecha >= izquierda and cadena[derecha] in (" ", "\t", "\n", "\r"):
        derecha -= 1
    return cadena[izquierda : derecha + 1]


def split_by_whitespace(cadena: str) -> list[str]:
    """Divide por cualquier espacio en blanco (equiv. a str.split sin argumento)."""
    palabras = []
    actual = ""
    for ch in cadena:
        if ch in (" ", "\t", "\n", "\r"):
            if actual:
                palabras.append(actual)
                actual = ""
        else:
            actual += ch
    if actual:
        palabras.append(actual)
    return palabras


def split_once(cadena: str, sep: str) -> tuple[str, str]:
    """Divide la cadena solo en la primera aparición de sep (equiv. a str.split(sep, 1))."""
    antes = ""
    i = 0
    while i < len(cadena) and cadena[i] != sep:
        antes += cadena[i]
        i += 1
    # No se encontró el separador
    if i == len(cadena):
        return antes, ""
    # Saltar el separador
    despues = cadena[i + 1 :]
    return antes, despues


def split_by_char(cadena: str, sep: str) -> list[str]:
    """Divide por un único carácter separador (sin usar str.split)."""
    partes = []
    actual = ""
    for ch in cadena:
        if ch == sep:
            partes.append(actual)
            actual = ""
        else:
            actual += ch
    partes.append(actual)
    return partes


def parse_yalp_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    tokens: list[str] = []
    productions: dict[str, list[list[str]]] = {}
    start_symbol: str | None = None
    current_lhs: str | None = None
    alternatives: list[list[str]] = []

    for idx in range(len(lines)):
        raw_line = lines[idx]
        line = trim(raw_line)

        # Verifica si inicia con %token
        if str_startswith(line, "%token"):
            partes = split_by_whitespace(line)
            i = 1
            while i < len(partes):
                tokens.append(partes[i])
                i += 1
            continue

        # Comentarios, líneas vacías, o IGNORE
        if line == "":
            continue
        if str_startswith(line, "/*"):
            continue
        if str_startswith(line, "IGNORE"):
            continue

        # Producción con ':'
        i = 0
        tiene_dos_puntos = False
        while i < len(line):
            if line[i] == ":":
                tiene_dos_puntos = True
                break
            i += 1

        if tiene_dos_puntos:
            if current_lhs is not None and len(alternatives) > 0:
                productions[current_lhs] = alternatives
                alternatives = []

            lhs_raw, rhs_raw = split_once(line, ":")
            lhs = trim(lhs_raw)
            rhs = trim(rhs_raw)
            current_lhs = lhs

            if start_symbol is None:
                start_symbol = lhs

            if rhs != "":
                rhs_alts = split_by_char(rhs, "|")
                j = 0
                while j < len(rhs_alts):
                    alt_line = trim(rhs_alts[j])
                    alt_tokens = split_by_whitespace(alt_line)
                    if len(alt_tokens) > 0:
                        alternatives.append(alt_tokens)
                    j += 1
            continue

        # Alternativa con |
        if str_startswith(line, "|"):
            alt = ""
            j = 1
            while j < len(line):
                alt += line[j]
                j += 1
            alt = trim(alt)
            alt_tokens = split_by_whitespace(alt)
            if len(alt_tokens) > 0:
                alternatives.append(alt_tokens)
            continue

        # Fin de producción con ;
        if str_startswith(line, ";"):
            if current_lhs is not None and len(alternatives) > 0:
                productions[current_lhs] = alternatives
            current_lhs = None
            alternatives = []
            continue

        # Otra alternativa válida
        if current_lhs is not None and line != "":
            alt_tokens = split_by_whitespace(line)
            if len(alt_tokens) > 0:
                alternatives.append(alt_tokens)

    # Agregar la última producción si quedó pendiente
    if current_lhs is not None and len(alternatives) > 0:
        productions[current_lhs] = alternatives

    # Inyectar producción inicial extendida S' → S
    if start_symbol in ("general", "p"):
        productions["S"] = [["S", start_symbol], [start_symbol]]
        base_start = "S"
    else:
        base_start = start_symbol

    start_symbol_aug = base_start + "'"
    while start_symbol_aug in productions:
        start_symbol_aug += "'"

    productions[start_symbol_aug] = [[base_start]]

    return tokens, productions, start_symbol_aug, base_start




def is_all_digits(cadena: str) -> bool:
    """Verifica si la cadena consiste solo de dígitos (sin usar funciones de librerías)."""
    if cadena == "":
        return False
    for c in cadena:
        if c < "0" or c > "9":
            return False
    return True

def convertir_a_entero(cadena: str) -> int:
    """Convierte manualmente una cadena de dígitos a entero (sin usar int())."""
    resultado = 0
    for c in cadena:
        resultado = resultado * 10 + (ord(c) - ord("0"))
    return resultado

def infer_token_map_from_pickle(dfa_pickle_path: str, tokens_declarados: list[str]) -> dict[str, str]:
    """
    Infiera dinámicamente el mapeo símbolo → nombre_token desde el AFD y los tokens %declarados en .yalp.
    Ahora acepta tanto nombres literales como valores ASCII.
    """
    import pickle
    with open(dfa_pickle_path, "rb") as f:
        afd = pickle.load(f)

    symbol_token_map = {}
    usados = []  # Tokens ya asociados

    acciones = afd["token_actions"]
    claves_estado = list(acciones.keys())

    for clave_estado in claves_estado:
        estado = acciones[clave_estado]
        if "merged" in estado:
            merged = estado["merged"]
            for m in merged:
                token_str = merged[m]
                # Si es ASCII (solo dígitos)
                if is_all_digits(token_str):
                    ascii_val = convertir_a_entero(token_str)
                    simbolo = chr(ascii_val)
                else:
                    simbolo = token_str  # nombre literal (ej: PLUS, MINUS, etc)
                # Buscar el primer token disponible que no esté usado
                for tk in tokens_declarados:
                    if tk not in usados and (tk == simbolo or tk.upper() == simbolo.upper()):
                        symbol_token_map[simbolo] = tk
                        usados.append(tk)
                        break
    print(">>> TOKEN_MAP INFERIDO DINÁMICAMENTE:", symbol_token_map)
    return symbol_token_map





def save_json(data, filename):
    import json

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    def convert(obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convert(data), f, indent=2, ensure_ascii=False)


def save_pickle(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def save_parser_output(actions, accepted, error_msg, input_tokens, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== Simulación del parser SLR(1) ===\n")
        f.write("Cadena de entrada (tokens): " + " ".join(input_tokens) + "\n\n")
        f.write("=== Lista de acciones del parser ===\n")
        for idx, act in enumerate(actions):
            f.write(f"{idx + 1}: {act}\n")

        f.write("\n=== Resultado final ===\n")
        if accepted:
            f.write("ACCEPT\n")
        else:
            f.write("ERROR\n")
            if error_msg:
                f.write(f"Detalles del error:\n{error_msg}\n")


# --- MAIN INTEGRADO  ---
def main(yalp_path, source_file_path, dfa_pickle_path, output_dir="output"):
    # Rutas de salida
    lr0_dir = os.path.join(output_dir, "LR0")
    ff_dir = os.path.join(output_dir, "first_follow")
    slr_dir = os.path.join(output_dir, "SLR")
    tokens, productions, augmented_start, start_symbol = parse_yalp_file(yalp_path)

    token_map = infer_token_map_from_pickle(dfa_pickle_path, tokens)

    # 2. Construir el automata LR(0)
    grammar = Grammar(productions, augmented_start)
    states, transitions, grammar = lr0_items(grammar)
    save_pickle((states, transitions), f"{lr0_dir}/lr0_states_transitions.pickle")
    visualize_lr0_automaton(
        states, transitions, grammar, filename=f"{lr0_dir}/lr0_automaton"
    )

    # 3. Calcular FIRST y FOLLOW
    first = compute_first(productions)
    follow = compute_follow(productions, first, start_symbol, token_map, tokens)

    # HACK: fuerza el SEMICOLON en FOLLOW(expression) si aparece en general
    if 'general' in productions:
        for prod in productions['general']:
            for i, sym in enumerate(prod):
                if sym == 'expression':
                    # Busca si luego de expression viene SEMICOLON
                    if i + 1 < len(prod) and prod[i + 1] == 'SEMICOLON':
                        follow['expression'].add('SEMICOLON')

    # === DEBUG: IMPRIMIR FOLLOW SETS ===
    print("\n=== FOLLOW SETS DEBUG ===")
    for nt, follow_set in follow.items():
        print(f"FOLLOW({nt}) = {follow_set}")

    save_pickle((first, follow), f"{ff_dir}/first_follow.pickle")
    save_json(first, f"{ff_dir}/first.json")
    save_json(follow, f"{ff_dir}/follow.json")

    # 4. Enumerar producciones
    print("\n=== Producciones enumeradas ===")
    productions_list = enumerate_productions(grammar.productions, grammar.start_symbol)

    save_pickle(productions_list, f"{slr_dir}/productions_enum.pickle")
    for prod_idx, lhs, rhs in productions_list:
        print(f"{prod_idx}: {lhs} → {' '.join(rhs)}")


    # 5. Construir tabla SLR(1)
    productions_enum = productions_list

    action_table, goto_table = compute_slr_table(
        grammar,
        first,
        follow,
        states,
        transitions,
        productions_enum,
        tokens,
        list(productions.keys()),
        token_map
    )
    save_slr_table(action_table, goto_table, filename=f"{slr_dir}/slr_table")

    print("\n=== Tabla SLR ACTION ===")
    for state, actions in action_table.items():
        for token, action in actions.items():
            if action is not None:
                print(f"Estado {state}, token {token}: {action}")

    print("\n=== Tabla SLR GOTO ===")
    for state, gotos in goto_table.items():
        for nt, next_state in gotos.items():
            if next_state is not None:
                print(f"Estado {state}, no-terminal {nt}: {next_state}")

    print("\n=== FIRST SETS DEBUG ===")
    for nt, first_set in first.items():
        print(f"FIRST({nt}) = {first_set}")

    with open(dfa_pickle_path, "rb") as f:
        dfa = pickle.load(f)

    with open(source_file_path, "r", encoding="utf-8") as fin:
        input_text = fin.read()

    # GENERADOR PRODUCTOR DE TOKENS
    def token_stream_gen():
        for token, lexema in lex(input_text, dfa):
            if token not in ("WHITESPACE", "WS", "TAB", "ENTER"):
                yield (token, lexema)

    # --- PASA EL GENERADOR DIRECTAMENTE AL PARSER ---
    accepted, actions, error_msg = simulate_slr_parser(
        action_table, goto_table, productions_enum, token_stream_gen(), start_symbol
    )

    # Para mostrar los tokens consumidos (solo para el reporte, no para el parser)
    tokens_for_parser = [
        token for token, _ in lex(input_text, dfa)
        if token not in ("WHITESPACE", "WS", "TAB", "ENTER")
    ]


    parser_outfile = os.path.join(output_dir, "parser_output.txt")
    save_parser_output(actions, accepted, error_msg, tokens_for_parser, parser_outfile)
    print("TOKENS PARA EL PARSER:")
    for t, lexema in lex(input_text, dfa):
        print(f"Token: {t}, Lexema: '{lexema}'")

    print("Parser terminado →", "ACCEPTED" if accepted else "ERROR")
    print(f"Output escrito en: {parser_outfile}")


# --- ENTRYPOINT ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python parser.py <ruta_a_yalp> <archivo_fuente> <dfa_pickle>")
        print(
            "Ejemplo:\n  "
            "python parser.py ../yalpfiles/slr-test.yalp "
            "../test/test_num.txt "
            "../lexers/lexer-test.pickle"
        )
        sys.exit(1)

    yalp_path = sys.argv[1]
    source_file_path = sys.argv[2]
    dfa_pickle_path = sys.argv[3]
    main(yalp_path, source_file_path, dfa_pickle_path)
