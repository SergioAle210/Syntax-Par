import json
import pickle
import itertools
from graphviz import Digraph
import os
import tok

from regexpToAFD import (
    toPostFix,
    build_syntax_tree,
    construct_afd,
    print_afd,
    print_mini_afd,
    minimize_afd,
    visualize_afd,
    visualize_minimized_afd,
)
from yalex_utils import (
    parse_yalex,
    expand_regex,
    expand_bracket_ranges,
    escape_token_literals,
    convert_plus_operator,
    convert_optional_operator,
    simplify_expression,
    attach_markers_to_final_regexp,
    process_regexp,
    compute_symbol_code,
)


def manual_join(strings: list, sep: str) -> str:
    """
    Concatena las cadenas en 'strings' utilizando 'sep' como separador,
    sin usar el método join.
    """
    result = ""
    for i in range(len(strings)):
        if i > 0:
            result += sep
        result += strings[i]
    return result


def make_json_serializable(afd):
    """
    Transforma el diccionario AFD en uno que sea serializable a JSON.
    """
    # Convertir sets de estados a listas
    json_states = {state: sorted(list(group)) for state, group in afd["states"].items()}

    # Convertir las claves tupla de las transiciones a una cadena "estado,símbolo"
    json_transitions = {
        "{},{}".format(k[0], k[1]): v for k, v in afd["transitions"].items()
    }

    # Los estados de aceptación ya vienen como lista
    json_accepting_states = afd["accepting_states"]

    # El estado inicial es una cadena
    json_initial_state = afd["initial_state"]

    # Para token_actions, si es el mapping minimizado (con "merged" y "orig")
    json_token_actions = {}
    for state, mapping in afd["token_actions"].items():
        # Si mapping es un dict con "merged" y "orig", lo convertimos:
        if isinstance(mapping, dict) and "merged" in mapping:
            merged = {str(marker): token for marker, token in mapping["merged"].items()}
            orig = {
                old_state: {str(marker): token for marker, token in m.items()}
                for old_state, m in mapping.get("orig", {}).items()
            }
            json_token_actions[state] = {"merged": merged, "orig": orig}
        else:
            # Caso simple
            json_token_actions[state] = {
                str(marker): token for marker, token in mapping.items()
            }

    return {
        "states": json_states,
        "transitions": json_transitions,
        "accepting_states": json_accepting_states,
        "initial_state": json_initial_state,
        "token_actions": json_token_actions,
    }


def visualize_syntax_tree(root, route, file_format="png"):
    """
    Genera y renderiza un grafo que representa el árbol de sintaxis (expresión)
    obtenido a partir de la especificación de tokens.

    Se guarda en la carpeta "./grafos/<route>/arbol_expresion".

    Parámetros:
      - root: nodo raíz del árbol de sintaxis (resultado de build_syntax_tree).
      - route: nombre base (por ejemplo, el nombre del archivo YAL sin extensión).
      - file_format: formato de la imagen de salida (ej. "png", "pdf").
    """
    # Construir el directorio de salida basado en el nombre del archivo YAL
    output_dir = os.path.join(".", "grafos", route, "arbol_expresion")
    os.makedirs(output_dir, exist_ok=True)

    dot = Digraph(comment="Árbol de Expresión", format=file_format)
    dot.attr(rankdir="TB")
    dot.attr(size="10,7", ratio="fill", dpi="300")

    counter = [1]

    def add_node(node):
        node_id = str(counter[0])
        counter[0] += 1
        label = f"Valor: {node.value}"
        if node.position is not None:
            label += f"\nPos: {node.position}"
        dot.node(node_id, label)
        if node.left:
            left_id = add_node(node.left)
            dot.edge(node_id, left_id)
        if node.right:
            right_id = add_node(node.right)
            dot.edge(node_id, right_id)
        return node_id

    add_node(root)
    # Especificamos un nombre de archivo para la imagen (sin extensión)
    output_path = os.path.join(output_dir, "arbol_expresion")
    dot.render(output_path, view=False)


if __name__ == "__main__":
    # 1. Leer y parsear el .yal
    route = "slr-4"
    yal_path = os.path.join("../spec/yalfiles", f"{route}.yal")
    result = parse_yalex(yal_path)

    # 2. Separar reglas / acciones y obtener símbolo literal
    regex_alt, action_alt = [], []
    for rule, act in result["rules"]:
        regex_alt.append(rule)
        action_alt.append(act)

    # 3-9. Pre-procesamiento de la ER combinada
    combined = "(" + manual_join(regex_alt, ")|(") + ")"
    expanded = expand_regex(combined, result["definitions"])
    brackets = expand_bracket_ranges(expanded)
    processed = process_regexp(brackets)
    escaped = escape_token_literals(processed)
    plus_conv = convert_plus_operator(escaped)
    opt_conv = convert_optional_operator(plus_conv)
    simplified = simplify_expression(opt_conv)

    # print("\nSimbolos:")
    # print(regex_alt)
    # print("\nAcciones:")
    # print(action_alt)

    # 10. Adjuntar marcadores y mapear (symCode / ws / id , TOKEN)
    final_expr, marker_map_full = attach_markers_to_final_regexp(
        simplified, action_alt, regex_alt
    )

    print("\nExpresión final:")
    print(final_expr)

    # 11. Convertir la expresión regular a postfix
    postfix = toPostFix(final_expr)
    # print("\nPostfix generado:")
    # print(postfix)

    # 12. Construir el árbol de sintaxis a partir del postfix
    syntax_tree, pos_sym_map = build_syntax_tree(postfix)

    # Visualizar el árbol de expresión y guardarlo en la misma carpeta que el AFD
    visualize_syntax_tree(syntax_tree, route, file_format="pdf")

    # 13. Construcción y minimización del AFD
    marker_to_action = {m: tkn for m, (_, tkn) in marker_map_full.items()}
    states, trans, acc, st_tok = construct_afd(
        syntax_tree, pos_sym_map, marker_to_action
    )
    new_states, new_trans, new_acc, new_init, new_tok = minimize_afd(
        states, trans, acc, st_tok
    )
    visualize_afd(states, trans, acc, route)
    visualize_minimized_afd(new_states, new_trans, new_acc, new_init, route)

    print("Tokens viejos generados")
    for state, token in st_tok.items():
        print(f"{state} -> {token}")
    print("Tokens generados:")
    for state, token in new_tok.items():
        print(f"{state} -> {token}")

    # 14. Mostrar
    print("\nMapping de marcadores:")
    for m, v in marker_map_full.items():
        print(f"{m}: {v}")

    # 15. token_to_symbol → dicta (códigoASCII / ws / id)
    token_to_symbol = {}
    for sym_code, tok_name in marker_map_full.values():
        if tok_name not in token_to_symbol:
            token_to_symbol[tok_name] = sym_code

    # 16. Conversión recursiva de new_tok a tuplas
    def convert(obj):
        if isinstance(obj, str):
            return (token_to_symbol.get(obj, ""), obj)
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        raise TypeError(f"Tipo inesperado: {type(obj)}")

    token_actions_final = {st: convert(tk) for st, tk in new_tok.items()}

    # 17. Diccionario final y exportación
    afd_minimized = {
        "states": new_states,
        "transitions": new_trans,
        "accepting_states": list(new_acc),
        "initial_state": new_init,
        "token_actions": token_actions_final,
    }

    if not os.path.exists("../lexers"):
        os.makedirs("./lexers", exist_ok=True)

    # Exportar a JSON para lexing (solo para visualizar)
    json_afd = make_json_serializable(afd_minimized)
    with open("../lexers/lexer-4.json", "w") as f:
        json.dump(json_afd, f, indent=4)
    print("\nDatos del AFD minimizado exportados a lexer.json.")

    with open("../lexers/lexer-4.pickle", "wb") as f:
        pickle.dump(afd_minimized, f)
    print("\nDatos del AFD minimizado exportados a lexer.pickle.")
