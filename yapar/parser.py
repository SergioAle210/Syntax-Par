import os
import pickle
import sys
from LR0 import Grammar, lr0_items, visualize_lr0_automaton
from first_follow import compute_first, compute_follow
from SLR import enumerate_productions, save_slr_table, compute_slr_table
from sim_slr import simulate_slr_parser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../lex")))
from lexer import lex  


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

    if i == len(cadena):
        return antes, ""
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

 
        if str_startswith(line, "%token"):
            partes = split_by_whitespace(line)
            i = 1
            while i < len(partes):
                tokens.append(partes[i])
                i += 1
            continue

        if line == "":
            continue
        if str_startswith(line, "/*"):
            continue
        if str_startswith(line, "IGNORE"):
            continue

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

        if str_startswith(line, ";"):
            if current_lhs is not None and len(alternatives) > 0:
                productions[current_lhs] = alternatives
            current_lhs = None
            alternatives = []
            continue

        if current_lhs is not None and line != "":
            alt_tokens = split_by_whitespace(line)
            if len(alt_tokens) > 0:
                alternatives.append(alt_tokens)

    if current_lhs is not None and len(alternatives) > 0:
        productions[current_lhs] = alternatives

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


def infer_token_map_from_pickle(
    pickle_path: str, tokens_decl: list[str]
) -> dict[str, str]:
    with open(pickle_path, "rb") as f:
        afd = pickle.load(f)

    symbol_token_map, usados = {}, set()

    for estado in afd["token_actions"].values():
        leaves = (
            estado["merged"]
            if isinstance(estado, dict) and "merged" in estado
            else estado
        )
        for sym_code, token_name in leaves.values():
            if token_name in usados:
                continue
            symbol = chr(int(sym_code)) if sym_code.isdigit() else sym_code
            if token_name in tokens_decl:
                symbol_token_map[symbol] = token_name
                usados.add(token_name)

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


def save_txt(lines: list[str], filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def dump_follow_sets(follow: dict, filename: str) -> None:
    líneas = [f"FOLLOW({nt}) = {sorted(vals)}" for nt, vals in follow.items()]
    save_txt(líneas, filename)


def dump_action_goto(action, goto, filename_prefix: str) -> None:
    # ACTION
    líneas = []
    for st, row in action.items():
        for tok, act in row.items():
            if act:
                líneas.append(f"STATE {st:3}  TOKEN {tok:10}  →  {act}")
    save_txt(líneas, filename_prefix + "_action.txt")
    # GOTO
    líneas = []
    for st, row in goto.items():
        for nt, nxt in row.items():
            if nxt is not None:
                líneas.append(f"STATE {st:3}  GOTO {nt:10}  →  {nxt}")
    save_txt(líneas, filename_prefix + "_goto.txt")


def basename_noext(path: str) -> str:  ### NEW ###
    name = os.path.basename(path)
    dot = name.rfind(".")
    return name[:dot] if dot != -1 else name


def main(
    yalp_path: str,
    source_file_path: str,
    dfa_pickle_path: str,
    output_dir: str = "output",
) -> None:

    if output_dir is None:
        tag = basename_noext(yalp_path)
        output_dir = os.path.join("output", tag)

    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "debug_log.txt")
    original_stdout = sys.stdout
    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = log_file  # todo print() ➜ debug_log.txt

    try:
        # 1. Rutas base
        lr0_dir = os.path.join(output_dir, "LR0")
        ff_dir = os.path.join(output_dir, "first_follow")
        slr_dir = os.path.join(output_dir, "SLR")

        # 2. Parsear el .yalp y AFD → token_map
        tokens, productions, augmented_start, start_symbol = parse_yalp_file(yalp_path)
        token_map = infer_token_map_from_pickle(dfa_pickle_path, tokens)

        # 3. Automata LR(0)
        grammar = Grammar(productions, augmented_start)
        states, transitions, _ = lr0_items(grammar)
        save_pickle((states, transitions), f"{lr0_dir}/lr0_states_transitions.pickle")
        visualize_lr0_automaton(
            states, transitions, grammar, filename=f"{lr0_dir}/lr0_automaton"
        )

        # 4. FIRST / FOLLOW
        first = compute_first(productions)
        follow = compute_follow(productions, first, start_symbol)

        save_pickle((first, follow), f"{ff_dir}/first_follow.pickle")
        save_json(first, f"{ff_dir}/first.json")
        save_json(follow, f"{ff_dir}/follow.json")
        dump_follow_sets(follow, f"{ff_dir}/follow.txt")  # TXT ordenado

        # 5. Enumerar producciones
        productions_list = enumerate_productions(
            grammar.productions, grammar.start_symbol
        )
        save_pickle(productions_list, f"{slr_dir}/productions_enum.pickle")
        save_txt(
            [f"{idx}: {lhs} → {' '.join(rhs)}" for idx, lhs, rhs in productions_list],
            f"{slr_dir}/productions_enum.txt",
        )

        # 6. Tabla SLR(1)
        action_table, goto_table = compute_slr_table(
            grammar,
            first,
            follow,
            states,
            transitions,
            productions_list,
            tokens,
            list(productions.keys()),
            token_map,
        )

        save_slr_table(action_table, goto_table, filename=f"{slr_dir}/slr_table")
        dump_action_goto(action_table, goto_table, f"{slr_dir}/slr_table")

        # 7. Preparar generador de tokens
        with open(dfa_pickle_path, "rb") as f:
            dfa = pickle.load(f)

        with open(source_file_path, "r", encoding="utf-8") as fin:
            input_text = fin.read()

        def token_stream_gen():
            skip = {"WHITESPACE", "WS", "ws", "TAB", "ENTER"}
            for (sym, token_name), lexeme in lex(input_text, dfa):
                if token_name in skip:
                    continue
                yield (token_name, lexeme)  # lo que el parser espera

        # 8. Simular el parser
        accepted, actions, error_msg = simulate_slr_parser(
            action_table, goto_table, productions_list, token_stream_gen(), start_symbol
        )

        # Lista de tokens legibles para el reporte
        tokens_for_parser = [
            token_name
            for (_, token_name), _ in lex(input_text, dfa)
            if token_name.upper() not in {"WHITESPACE", "WS", "TAB", "ENTER"}
        ]

        parser_outfile = os.path.join(output_dir, "parser_output.txt")
        save_parser_output(
            actions, accepted, error_msg, tokens_for_parser, parser_outfile
        )

        # 9. Resumen final (va al log)
        print("\nParser terminado →", "ACCEPTED" if accepted else "ERROR")
        print("Output escrito en :", parser_outfile)

    finally:
        # 10. Restaurar stdout y cerrar el log
        sys.stdout = original_stdout
        log_file.close()
        print(f"[INFO] Ejecución completada. Log detallado en {log_path}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Uso: python parser.py <ruta_a_yalp> <archivo_fuente> <dfa_pickle> [out_dir]"
        )
        sys.exit(1)

    yalp_path = sys.argv[1]
    source_file_path = sys.argv[2]
    dfa_pickle_path = sys.argv[3]
    out_dir_arg = sys.argv[4] if len(sys.argv) >= 5 else None

    main(yalp_path, source_file_path, dfa_pickle_path, out_dir_arg)
