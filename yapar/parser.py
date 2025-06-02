import os
import pickle
import sys

# --- IMPORTS DE TU PROYECTO ---
from LR0 import Grammar, lr0_items, visualize_lr0_automaton
from first_follow import compute_first, compute_follow
from SLR import enumerate_productions, save_slr_table, compute_slr_table
from sim_slr import simulate_slr_parser

# --- IMPORTAR EL LEXER ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../lex")))
from lexer import lex

# --- FUNCIÓN PARA PARSEAR .YALP ---
def parse_yalp_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    tokens = []
    productions = {}
    start_symbol = None
    current_lhs = None
    alternatives = []

    for line in lines:
        line = line.strip()

        # Parse tokens
        if line.startswith('%token'):
            tokens += line.split()[1:]

        # Ignorar líneas vacías o comentarios
        elif not line or line.startswith('/*') or line.startswith('IGNORE'):
            continue

        # LHS con definición
        elif ':' in line:
            if current_lhs is not None and alternatives:
                productions[current_lhs] = alternatives
                alternatives = []

            lhs, rhs = line.split(':', 1)
            lhs = lhs.strip()
            rhs = rhs.strip()
            current_lhs = lhs

            if start_symbol is None:
                start_symbol = lhs

            if rhs:
                if '|' in rhs:
                    for alt in rhs.split('|'):
                        alt = alt.strip()
                        if alt:
                            alternatives.append(alt.split())
                else:
                    alternatives.append(rhs.split())

        # Línea alternativa con '|'
        elif line.startswith('|'):
            alt = line[1:].strip()
            if alt:
                alternatives.append(alt.split())

        # Fin de producción con ';'
        elif line.startswith(';'):
            if current_lhs and alternatives:
                productions[current_lhs] = alternatives
                alternatives = []
                current_lhs = None

        # Alternativas continuadas en otra línea
        elif current_lhs and line:
            alternatives.append(line.split())

    # Última producción si quedó sin cerrar con ;
    if current_lhs and alternatives:
        productions[current_lhs] = alternatives

    # === Agregar producción aumentada ===
    augmented_start = start_symbol + "'"
    while augmented_start in productions:
        augmented_start += "'"

    # DEBUG
    print("Productions:", productions)
    return tokens, productions, start_symbol



def infer_token_map(tokens, productions):
    """
    Infiera el mapeo entre lexemas concretos (como '+', '*') y nombres simbólicos de tokens
    (como 'PLUS', 'TIMES'), utilizando los tokens definidos en %token.
    """
    # Mapeo clásico de símbolos a nombres comunes
    known_map = {
        '+': 'PLUS',
        '*': 'TIMES',
        '-': 'MINUS',
        '/': 'DIV',
        '(': 'LPAREN',
        ')': 'RPAREN',
        ';': 'SEMICOLON',
    }

    symbol_map = {}

    # Solo agregar si están efectivamente en los tokens declarados
    for sym, token_name in known_map.items():
        if token_name in tokens:
            symbol_map[sym] = token_name

    print(">>> TOKEN_MAP INFERIDO:", symbol_map)
    return symbol_map



# --- GUARDAR JSON ---
def save_json(data, filename):
    import json
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    def convert(obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        else:
            return obj
    data_conv = convert(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data_conv, f, indent=2, ensure_ascii=False)

# --- GUARDAR PICKLE ---
def save_pickle(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(data, f)

# --- GUARDAR OUTPUT DEL PARSER ---
def save_parser_output(actions, accepted, error_msg, input_tokens, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== Simulación del parser SLR(1) ===\n")
        f.write("Cadena de entrada (tokens): " + " ".join(input_tokens) + "\n\n")
        f.write("=== Lista de acciones del parser ===\n")
        for idx, act in enumerate(actions):
            f.write(f"{idx+1}: {act}\n")

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

    # 1. Parsear el archivo YALP
    tokens, productions, raw_start_symbol = parse_yalp_file(yalp_path)

    token_map = infer_token_map(tokens, productions)

    if raw_start_symbol == 'general':
        productions['S'] = [['general_list']]
        productions['general_list'] = [['general_list', 'general'], ['general']]
        start_symbol = 'S'
    else:
        start_symbol = raw_start_symbol

    # Aumentar después de haber decidido el start_symbol
    augmented_start = start_symbol + "'"
    while augmented_start in productions:
        augmented_start += "'"
    productions[augmented_start] = [[start_symbol]]




    # 2. Construir el automata LR(0)
    grammar = Grammar(productions, augmented_start)
    states, transitions, grammar = lr0_items(grammar)
    save_pickle((states, transitions), f"{lr0_dir}/lr0_states_transitions.pickle")
    visualize_lr0_automaton(states, transitions, grammar, filename=f"{lr0_dir}/lr0_automaton")

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
    productions_enum = [(idx, lhs, rhs) for idx, (lhs, rhs) in enumerate(productions_list)]
    action_table, goto_table = compute_slr_table(
        grammar,
        first,
        follow,
        states,
        transitions,
        productions_enum,
        tokens,
        list(productions.keys())
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
        action_table, goto_table, productions_enum, token_stream_gen()
    )

    # Para mostrar los tokens consumidos (solo para el reporte, no para el parser)
    tokens_for_parser = [token_map.get(token, token) for token, _ in lex(input_text, dfa) if token not in ("WHITESPACE", "WS", "TAB", "ENTER")]

    parser_outfile = os.path.join(output_dir, "parser_output.txt")
    save_parser_output(actions, accepted, error_msg, tokens_for_parser, parser_outfile)
    print("TOKENS PARA EL PARSER:")
    for t, lexema in lex(input_text, dfa):
        print(f"Token: {t}, Lexema: '{lexema}'")

    print("Parser terminado.")
    print("Resultado:", "ACCEPTED" if accepted else "ERROR")
    print(f"Output escrito en: {parser_outfile}")

# --- ENTRYPOINT ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Uso: python parser.py <ruta_a_yalp> <archivo_fuente> <dfa_pickle>")
        print("Ejemplo:")
        print("   python parser.py ../yalpfiles/slr-test.yalp ../test/test_num.txt ../lexers/lexer-test.pickle")
    else:
        yalp_path = sys.argv[1]
        source_file_path = sys.argv[2]
        dfa_pickle_path = sys.argv[3]
        main(yalp_path, source_file_path, dfa_pickle_path)
