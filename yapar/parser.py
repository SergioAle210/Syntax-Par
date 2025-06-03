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

    # Mapeo clásico para traducir símbolos concretos a nombres de token
    known_symbol_map = {
        "+": "PLUS",
        "*": "TIMES",
        "-": "MINUS",
        "/": "DIV",
        "(": "LPAREN",
        ")": "RPAREN",
        ";": "SEMICOLON",
        ":=": "ASSIGNOP",
        "<": "LT",
        "=": "EQ",
        ".": "POINT",
    }

    tokens: list[str] = []
    productions: dict[str, list[list[str]]] = {}
    start_symbol: str | None = None
    current_lhs: str | None = None
    alternatives: list[list[str]] = []

    for raw in lines:
        line = trim(raw)

        # %token ... ...
        if str_startswith(line, "%token"):
            partes = split_by_whitespace(line)
            # Saltamos el primer elemento ("%token")
            tokens += partes[1:]
            continue

        # comentarios, IGNORE, líneas vacías
        if line == "" or str_startswith(line, "/*") or str_startswith(line, "IGNORE"):
            continue

        # Nueva producción con ":"
        if ":" in line:
            # Guardar la anterior si existía
            if current_lhs is not None and alternatives:
                productions[current_lhs] = alternatives
                alternatives = []

            lhs_raw, rhs_raw = split_once(line, ":")
            lhs = trim(lhs_raw)
            rhs = trim(rhs_raw)
            current_lhs = lhs

            if start_symbol is None:
                start_symbol = lhs

            if rhs:  # puede venir algo tras los dos puntos
                rhs_alts = split_by_char(rhs, "|")
                for alt in rhs_alts:
                    alt_tokens = [
                        known_symbol_map.get(tok, tok)
                        for tok in split_by_whitespace(trim(alt))
                    ]
                    if alt_tokens:
                        alternatives.append(alt_tokens)
            continue

        # Alternativa con |
        if str_startswith(line, "|"):
            alt = trim(line[1:])
            alt_tokens = [
                known_symbol_map.get(tok, tok) for tok in split_by_whitespace(alt)
            ]
            if alt_tokens:
                alternatives.append(alt_tokens)
            continue

        # Fin de la producción con ;
        if str_startswith(line, ";"):
            if current_lhs and alternatives:
                productions[current_lhs] = alternatives
            current_lhs = None
            alternatives = []
            continue

        # Otra alternativa en la misma línea
        if current_lhs and line:
            alt_tokens = [
                known_symbol_map.get(tok, tok) for tok in split_by_whitespace(line)
            ]
            if alt_tokens:
                alternatives.append(alt_tokens)

    # Última producción pendiente
    if current_lhs and alternatives:
        productions[current_lhs] = alternatives

    # ── INYECTAR PRODUCCIÓN SUPERIOR SI ES NECESARIO ──
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


def infer_token_map(tokens, productions):
    """
    Infiera el mapeo entre lexemas concretos y nombres de tokens,
    usando la lista declarada con %token.
    """
    known_map = {
        "+": "PLUS",
        "*": "TIMES",
        "-": "MINUS",
        "/": "DIV",
        "(": "LPAREN",
        ")": "RPAREN",
        ";": "SEMICOLON",
    }
    symbol_map = {}
    for sym, token_name in known_map.items():
        # Solo incluir si efectivamente ese token existe
        for t in tokens:
            if t == token_name:
                symbol_map[sym] = token_name
                break
    print(">>> TOKEN_MAP INFERIDO:", symbol_map)
    return symbol_map


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

    token_map = infer_token_map(tokens, productions)

    # 2. Construir el automata LR(0)
    grammar = Grammar(productions, augmented_start)
    states, transitions, grammar = lr0_items(grammar)
    save_pickle((states, transitions), f"{lr0_dir}/lr0_states_transitions.pickle")
    visualize_lr0_automaton(
        states, transitions, grammar, filename=f"{lr0_dir}/lr0_automaton"
    )

    # 3. Calcular FIRST y FOLLOW
    first = compute_first(productions)
    follow = compute_follow(productions, first, start_symbol)

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
    for idx, (lhs, rhs) in enumerate(productions_list):
        print(f"{idx}: {lhs} → {' '.join(rhs)}")

    # 5. Construir tabla SLR(1)
    productions_enum = [
        (idx, lhs, rhs) for idx, (lhs, rhs) in enumerate(productions_list)
    ]
    action_table, goto_table = compute_slr_table(
        grammar,
        first,
        follow,
        states,
        transitions,
        productions_enum,
        tokens,
        list(productions.keys()),
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
                yield (token_map.get(token, token), lexema)

    # --- PASA EL GENERADOR DIRECTAMENTE AL PARSER ---
    accepted, actions, error_msg = simulate_slr_parser(
        action_table, goto_table, productions_enum, token_stream_gen(), start_symbol
    )

    # Para mostrar los tokens consumidos (solo para el reporte, no para el parser)
    tokens_for_parser = [
        token_map.get(token, token)
        for token, _ in lex(input_text, dfa)
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
