import json
import pickle
import itertools
from graphviz import Digraph
import os

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
    # 1. Parsear el archivo YAL (usando nuestra versión manual en yalex_utils)

    route = "slr-test"
    name_yalfile = route + ".yal"
    filepath = os.path.join("../spec/yalfiles", name_yalfile)

    result = parse_yalex(filepath)

    # 2. Extraer las reglas de tokens y acciones asociadas
    token_rules = result["rules"]
    regex_alternatives = [rule for rule, act in token_rules]
    action_alternatives = [act for rule, act in token_rules]

    # Construir la expresión combinada sin usar .join:
    # en lugar de: "(" + ")|(".join(regex_alternatives) + ")"
    combined_expr = "(" + manual_join(regex_alternatives, ")|(") + ")"
    print("Expresión combinada:")
    print(combined_expr)

    # 3. Expandir definiciones
    expr_expandida = expand_regex(combined_expr, result["definitions"])
    print("\nExpresión expandida:")
    print(expr_expandida)

    # 4. Expandir rangos en corchetes
    expr_con_brackets = expand_bracket_ranges(expr_expandida)

    # 5. Procesar la expresión para convertir literales a ASCII
    expr_procesada = process_regexp(expr_con_brackets)
    print("\nExpresión procesada (con literales convertidas a ASCII):")
    print(expr_procesada)

    # 6. Escapar literales que son metacaracteres
    expr_escapada = escape_token_literals(expr_procesada)

    # 7. Convertir operador +
    expr_convertida = convert_plus_operator(expr_escapada)

    # 8. Convertir operador ?
    expr_optional = convert_optional_operator(expr_convertida)

    # 9. Simplificar la expresión regular
    expr_simplificada = simplify_expression(expr_optional)

    # 10. Asignar marcadores a las acciones asociadas a los tokens
    final_expr, marker_mapping = attach_markers_to_final_regexp(
        expr_simplificada, regex_alternatives
    )

    print("\nExpresión final:")
    print(final_expr)

    # 11. Convertir la expresión regular a postfix
    postfix = toPostFix(final_expr)
    print("\nPostfix generado:")
    print(postfix)
    print("\nMapping de marcadores (acciones):")
    print(marker_mapping)

    # 12. Construir el árbol de sintaxis a partir del postfix
    syntax_tree, position_symbol_map = build_syntax_tree(postfix)

    # Visualizar el árbol de expresión y guardarlo en la misma carpeta que el AFD
    visualize_syntax_tree(syntax_tree, route, file_format="pdf")

    # 13. Construir el AFD a partir del árbol de sintaxis (usando marker_mapping)
    states, transitions, accepting_states, state_token_mapping = construct_afd(
        syntax_tree, position_symbol_map, marker_mapping
    )

    # Minimizar y visualizar el AFD
    (
        new_states,
        new_transitions,
        new_accepting_states,
        new_initial_state,
        new_token_actions,
    ) = minimize_afd(states, transitions, accepting_states, state_token_mapping)
    visualize_afd(states, transitions, accepting_states, route)
    visualize_minimized_afd(
        new_states,
        new_transitions,
        new_accepting_states,
        new_initial_state,
        route,
    )

    print("Tokens viejos generados")
    for state, token in state_token_mapping.items():
        print(f"{state} -> {token}")
    print("Tokens generados:")
    for state, token in new_token_actions.items():
        print(f"{state} -> {token}")

    # Diccionario final del AFD minimizado
    afd_minimized = {
        "states": new_states,
        "transitions": new_transitions,
        "accepting_states": list(new_accepting_states),
        "initial_state": new_initial_state,
        "token_actions": new_token_actions,  # Mapping minimizado (con "merged" y "orig")
    }

    if not os.path.exists("../lexers"):
        os.makedirs("./lexers", exist_ok=True)

    # Exportar a JSON para lexing (solo para visualizar)
    json_afd = make_json_serializable(afd_minimized)
    with open("../lexers/lexer-test.json", "w") as f:
        json.dump(json_afd, f, indent=4)
    print("\nDatos del AFD minimizado exportados a lexer.json.")

    with open("../lexers/lexer-test.pickle", "wb") as f:
        pickle.dump(afd_minimized, f)
    print("\nDatos del AFD minimizado exportados a lexer.pickle.")
