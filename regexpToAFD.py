# Laboratorio - Construcción directa de un AFD a partir de una expresión regular
# Andre Marroquin 22266
# Rodrigo Mansilla
# Sergio Orellana 221122

# Importamos las librerías necesarias
import itertools
from colorama import Fore, Style
import graphviz
import os
import string
from yalex_utils import expand_underscore

# Funciones auxiliares para manejo de cadenas sin métodos nativos


def manual_split_by_space(s: str) -> list:
    """Divide la cadena s en tokens separados por espacios, sin usar .split()."""
    result = []
    current = ""
    for ch in s:
        if ch == " ":
            if current != "":
                result.append(current)
                current = ""
        else:
            current += ch
    if current != "":
        result.append(current)
    return result


def manual_join(strings: list, sep: str) -> str:
    """Une las cadenas de la lista strings utilizando sep como separador, sin usar .join()."""
    result = ""
    for i in range(len(strings)):
        if i > 0:
            result += sep
        result += strings[i]
    return result


def custom_is_digit(c: str) -> bool:
    """
    Retorna True si el carácter c es un dígito ('0' a '9'), sin usar isdigit().
    """
    o = ord(c)
    return 48 <= o <= 57


def custom_all_digits(s: str) -> bool:
    """
    Retorna True si todos los caracteres de s son dígitos.
    """
    for ch in s:
        if not custom_is_digit(ch):
            return False
    return True


def custom_to_int(s: str) -> int:
    """
    Convierte manualmente una cadena s compuesta solo por dígitos en un entero.
    """
    value = 0
    for ch in s:
        value = value * 10 + (ord(ch) - 48)
    return value


def custom_trim(s: str) -> str:
    """
    Elimina manualmente espacios en blanco (espacios, tabs, saltos de línea)
    al inicio y final de la cadena s, sin usar .strip().
    """
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


def custom_find(text: str, pattern: str, start: int = 0) -> int:
    """
    Busca la primera ocurrencia de 'pattern' en 'text' a partir de 'start', sin usar .find().
    Retorna el índice o -1 si no se encuentra.
    """
    pat_len = 0
    for _ in pattern:
        pat_len += 1
    text_len = 0
    for _ in text:
        text_len += 1
    for i in range(start, text_len - pat_len + 1):
        found = True
        j = 0
        while j < pat_len:
            if text[i + j] != pattern[j]:
                found = False
                break
            j += 1
        if found:
            return i
    return -1


def custom_split_lines(text: str) -> list:
    """
    Separa el texto en líneas usando el carácter de salto de línea, sin usar .splitlines().
    """
    lines = []
    current_line = ""
    for ch in text:
        if ch == "\n":
            lines.append(current_line)
            current_line = ""
        else:
            current_line += ch
    if current_line != "":
        lines.append(current_line)
    return lines


def custom_startswith(s: str, prefix: str, pos: int = 0) -> bool:
    """
    Verifica manualmente si la cadena s comienza con prefix a partir de la posición pos,
    sin usar .startswith().
    """
    i = 0
    while i < len(prefix):
        if pos + i >= len(s) or s[pos + i] != prefix[i]:
            return False
        i += 1
    return True


def is_alnum(ch: str) -> bool:
    """
    Retorna True si el carácter ch es alfanumérico (A-Z, a-z o 0-9) sin usar .isalnum().
    """
    o = ord(ch)
    return (48 <= o <= 57) or (65 <= o <= 90) or (97 <= o <= 122)


# Clase Nodo encargada de inicializar los valores de los nodos en el árbol de sintaxis
class Node:
    """
    Esta parte se hizo con ayuda de LLMs para poder entender mejor el funcionamiento de los nodos

    Promt utilizado:

    Could you give me a structure or class of node type in python where I can represent the important parts of an AFD with direct construction, I want it to have, the value of the node, if it has children (both left and right), if it is voidable, a set of sets for first pos, another for last pos and another for the identification of the position.
    """

    def __init__(self, value, left=None, right=None):
        self.value = value  # Valor del nodo
        self.left = left  # Nodo izquierdo
        self.right = right  # Nodo derecho
        self.nullable = False  # Esto funciona para representar si es anulable o no
        self.firstpos = set()  # Contiene el conjunto de posiciones de primera-pos
        self.lastpos = set()  # # Contiene el conjunto de posiciones de última-pos
        self.position = None  # Sirve para identificar la posición del nodo


# Definimos las precedencias de los operadores
precedence = {"|": 1, ".": 2, "*": 3}


def is_marker(token: str) -> bool:
    r"""
    Retorna True si el token es una secuencia de dígitos (verificado manualmente)
    y su valor numérico es >= 1000.
    """
    if token == "":
        return False
    if not custom_all_digits(token):
        return False
    if custom_to_int(token) >= 1000:
        return True
    return False


def is_operand_token(token: str) -> bool:
    r"""
    Retorna True si el token se considera operando:
      - Es una cadena no vacía en la que cada carácter es alfanumérico (manual) o '_'
      - O es una secuencia escapada, es decir, comienza con "\".
    """
    if token == "":
        return False
    if token[0] == "\\":
        return True
    for ch in token:
        if not (is_alnum(ch) or ch == "λ"):
            return False
    return True


def tokenize_for_concat(infix: str) -> list:
    """
    Tokeniza la expresión infija a nivel de tokens.
    Se ignoran los espacios (comparando manualmente con " \t\n\r").
    Se agrupan los dígitos en un solo token usando custom_is_digit.
    Además, se tratan los operadores especiales, las secuencias escapadas y
    se deja el carácter '_' sin convertir a su valor ASCII.
    """
    tokens = []
    i = 0
    while i < len(infix):
        if infix[i] in " \t\n\r":
            i += 1
            continue
        elif infix[i] == "_":
            tokens.append(expand_underscore())
            i += 1
        # Si se detecta el delimitador '$', se toma todo hasta el siguiente '$'
        elif infix[i] == "$":
            token = ""
            i += 1  # Saltar el '$' de apertura
            while i < len(infix) and infix[i] != "$":
                token += infix[i]
                i += 1
            if i < len(infix) and infix[i] == "$":
                i += 1  # Saltar el '$' de cierre
            tokens.append(token)  # Agrega el contenido sin los delimitadores
        elif custom_is_digit(infix[i]):
            num = ""
            while i < len(infix) and custom_is_digit(infix[i]):
                num += infix[i]
                i += 1
            tokens.append(num)
        elif infix[i] in {"|", ".", "*", "(", ")"}:
            tokens.append(infix[i])
            i += 1
        elif infix[i] == "\\" and i + 1 < len(infix):
            tokens.append(infix[i] + infix[i + 1])
            i += 2
        elif infix[i] == "λ":
            # Deja el lambda tal cual, sin convertirlo a ASCII.
            tokens.append("λ")
            i += 1
        else:
            # Para otros caracteres, se usa su valor ASCII (convertido manualmente)
            tokens.append(str(ord(infix[i])))
            i += 1
    return tokens


def insert_concatenation_operators(infix: str) -> str:
    """
    Inserta el operador de concatenación (".") en la cadena infija.
    Se utiliza tokenize_for_concat para obtener la lista de tokens; si un token es seguido por un
    operando o por "(", se inserta un punto.
    """
    tokens = tokenize_for_concat(infix)
    result_tokens = []
    n = len(tokens)
    for i in range(n):
        result_tokens.append(tokens[i])
        if i < n - 1:
            # Insertar punto si el token actual no es un operador y el siguiente no es un operador o "("
            if is_marker(tokens[i]) and is_marker(tokens[i + 1]):
                continue

            # Insertar punto si el token actual no es un operador y el siguiente no es un operador o "("
            elif is_marker(tokens[i]) and (
                is_operand_token(tokens[i + 1]) or tokens[i + 1] == "("
            ):
                result_tokens.append(".")

            # Insertar punto si el token actual no es un operador y el siguiente no es un operador o "("
            elif (
                not is_marker(tokens[i])
                and is_operand_token(tokens[i])
                and (is_operand_token(tokens[i + 1]) or tokens[i + 1] == "(")
            ):
                result_tokens.append(".")

            # Insertar punto si el token actual no es un operador y el siguiente no es un operador o "("
            elif tokens[i] in {")", "*"} and (
                is_operand_token(tokens[i + 1]) or tokens[i + 1] == "("
            ):
                result_tokens.append(".")

    # Insertar punto si el token actual no es un operador y el siguiente no es un operador o "("
    return manual_join(result_tokens, "")


def toPostFix(infixExpression: str) -> str:
    """
    Convierte la expresión regular en notación infija a notación postfix.
    Se inserta el operador de concatenación, se tokeniza manualmente y se aplica el algoritmo
    de conversión, tratando los marcadores (números ≥ 1000) como elementos atómicos.
    """

    # Primero se inserta el operador de concatenación
    infix_with_concat = insert_concatenation_operators(infixExpression)
    print("Expresión regular con concatenación:", infix_with_concat)

    tokens = tokenize_for_concat(infix_with_concat)
    output = []
    operators = []
    for token in tokens:
        if token in {"|", ".", "*"}:
            # Es operador: se aplica la precedencia
            while (
                operators
                and operators[-1] != "("
                and operators[-1] in {"|", ".", "*"}
                and precedence[operators[-1]] >= precedence[token]
            ):
                output.append(operators.pop())
            operators.append(token)
        elif token == "(":
            operators.append(token)
        elif token == ")":
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            if operators and operators[-1] == "(":
                operators.pop()
        else:
            # Es operando (incluye marcadores y números ASCII)
            output.append(token)
    while operators:
        op = operators.pop()
        if op not in {"(", ")"}:
            output.append(op)
    return manual_join(output, " ")


def is_operand(token: str) -> bool:
    """
    Retorna True si el token no es uno de los operadores ("|", ".", "*"),
    por lo que se considera operando.
    """
    return token not in {"|", ".", "*"}


def build_syntax_tree(postfix: str):
    """
    Construye el árbol de sintaxis a partir de la expresión en notación postfix.
    Se asume que la expresión postfix es una cadena de tokens separados por espacios.
    Cada token representa un operando (literal o marcador) o un operador (|, . o *).
    """
    # Dividir la expresión postfix en tokens
    tokens = manual_split_by_space(postfix)
    stack = []
    pos_counter = iter(range(1, 10**6))  # Contador para posiciones únicas
    position_symbol_map = {}
    for token in tokens:
        if is_operand(token):
            # Es un operando: creamos un nodo y le asignamos posición
            node = Node(token)
            node.position = next(pos_counter)
            node.firstpos.add(node.position)
            node.lastpos.add(node.position)
            position_symbol_map[node.position] = token
            stack.append(node)
        elif token == "*":
            # Operador de Kleene: se toma el último nodo de la pila
            child = stack.pop()
            node = Node("*", left=child)
            node.nullable = True
            node.firstpos = child.firstpos.copy()
            node.lastpos = child.lastpos.copy()
            stack.append(node)
        elif token == ".":
            # Concatenación: se toman los dos últimos nodos de la pila
            right = stack.pop()
            left = stack.pop()
            node = Node(".", left, right)
            node.nullable = left.nullable and right.nullable
            if left.nullable:
                node.firstpos = left.firstpos | right.firstpos
            else:
                node.firstpos = left.firstpos.copy()
            if right.nullable:
                node.lastpos = right.lastpos | left.lastpos
            else:
                node.lastpos = right.lastpos.copy()
            stack.append(node)
        elif token == "|":
            right = stack.pop()
            left = stack.pop()
            node = Node("|", left, right)
            node.nullable = left.nullable or right.nullable
            node.firstpos = left.firstpos | right.firstpos
            node.lastpos = left.lastpos | right.lastpos
            stack.append(node)

    # Al finalizar, la pila debe contener el nodo raíz
    return stack.pop(), position_symbol_map


# Función que calcula el siguientepos
def compute_followpos(node, followpos):
    """
    Calcula las followpos de cada nodo hoja en el árbol de sintaxis.
    Para la concatenación y la cerradura de Kleene se propagan las posiciones correspondientes.
    """
    if node is None:
        return

    # Si el nodo es una concatenación
    if node.value == ".":
        # Entonces para cada posición en lastpos del hijo izquierdo se encuentran en las posiciones de firstpos del hijo derecho
        for pos in node.left.lastpos:
            followpos[pos] |= node.right.firstpos

    # Si el nodo es una cerradura de Kleene
    if node.value == "*":
        # Entonces para cada posición en lastpos del hijo se encuentran en las posiciones de firstpos del hijo
        for pos in node.lastpos:
            followpos[pos] |= node.firstpos

    # Llamamos recursivamente a la función para el hijo izquierdo y el hijo derecho
    compute_followpos(node.left, followpos)
    compute_followpos(node.right, followpos)


def epsilon_closure(state, position_symbol_map, followpos):
    """
    Dado un conjunto de posiciones 'state', calcula su ε-cerradura (lambda-closure):
    incluye todas las posiciones alcanzables a través de transiciones lambda ("λ").
    """
    closure = set(state)
    stack = list(state)
    while stack:
        pos = stack.pop()
        if position_symbol_map.get(pos) == "λ":
            for fp in followpos.get(pos, set()):
                if fp not in closure:
                    closure.add(fp)
                    stack.append(fp)
    return closure


# Función que construye el AFD a partir del árbol de sintaxis.
# Parámetros:
# - root: Nodo raíz del árbol de sintaxis.
# - position_symbol_map: Diccionario que mapea las posiciones numéricas a los símbolos de la expresión regular.
def construct_afd(root, position_symbol_map, marker_mapping):
    # Inicializamos el diccionario de followpos, donde cada posición tendrá su conjunto de followpos.
    followpos = {pos: set() for pos in position_symbol_map}
    # Calculamos el conjunto de followpos para cada posición en el árbol de sintaxis.
    compute_followpos(root, followpos)

    # Calcular la ε-cerradura del firstpos de la raíz
    initial_closure = epsilon_closure(root.firstpos, position_symbol_map, followpos)

    # Diccionario que almacenará los estados del AFD.
    states = {}
    # La cola inicia con la ε-cerradura del firstpos (convertida a frozenset para usarla como clave)
    state_queue = [frozenset(initial_closure)]
    # Diccionario de transiciones, donde la clave es una tupla (estado, símbolo) y el valor es el siguiente estado.
    transitions = {}
    # Diccionario que asignará nombres a los estados.
    state_names = {}
    # Generador de nombres para los estados (A, B, C, ...).
    current_name = itertools.count(ord("A"))
    # Conjunto de estados de aceptación.
    accepting_states = set()

    # Bucle que procesa cada estado en la cola de estados pendientes.
    while state_queue:
        # Extraemos el primer estado de la cola.
        state = state_queue.pop(0)
        if not state:
            continue  # Si el estado está vacío, lo ignoramos.

        # Si el estado no está registrado en el diccionario de estados, lo agregamos.
        if state not in state_names:
            # Asignamos un nombre al estado (ejemplo: 'A', 'B', 'C'...).
            state_names[state] = chr(next(current_name))
            # Guardamos el estado en el diccionario de estados.
            states[state_names[state]] = state

        # Obtenemos el estado efectivo (la ε-cerradura del estado actual)
        effective_state = epsilon_closure(state, position_symbol_map, followpos)

        # Diccionario temporal para mapear cada símbolo a su conjunto de followpos.
        symbol_map = {}
        # Para cada posición en el estado efectivo...
        for pos in effective_state:
            symbol = position_symbol_map.get(pos)
            # Consideramos solo símbolos "reales": descartamos marcadores y "λ"
            if symbol and not is_marker(symbol) and symbol != "λ":
                if symbol not in symbol_map:
                    symbol_map[symbol] = set()
                # Agregamos los followpos de esta posición al conjunto de transiciones del símbolo.
                symbol_map[symbol] |= followpos.get(pos, set())

        # Para cada símbolo (no λ) se calcula el siguiente estado (ε-cerradura del movimiento)
        for symbol, next_set in symbol_map.items():
            # Calculamos la ε-cerradura del siguiente conjunto de posiciones.
            next_closure = epsilon_closure(next_set, position_symbol_map, followpos)

            # Si el conjunto resultante no está vacío, lo procesamos.
            next_closure = frozenset(next_closure)
            if not next_closure:
                continue

            # Si el siguiente estado no está registrado, lo agregamos a la cola de procesamiento.
            if next_closure not in state_names:
                state_queue.append(next_closure)  # Agregamos el estado a la cola
                state_names[next_closure] = chr(
                    next(current_name)
                )  # Asignamos un nombre al estado
                states[state_names[next_closure]] = (
                    next_closure  # Guardamos el estado en el diccionario
                )
            transitions[(state_names[state], symbol)] = state_names[
                next_closure
            ]  # Guardamos la transición

    # Identificamos los estados de aceptación. Ahora, en lugar de solo mirar las posiciones
    # directas, usamos la ε-cerradura para incluir las transiciones lambda.
    for state_name, positions in states.items():
        # Usamos la ε-cerradura para asegurarnos de incluir marcadores alcanzables vía λ ya que este es mi simbolo blanco
        effective_positions = epsilon_closure(positions, position_symbol_map, followpos)

        # Si alguna de las posiciones efectivas es un marcador, agregamos el estado a los estados de aceptación.
        if any(
            is_marker(position_symbol_map.get(pos))
            for pos in effective_positions
            if position_symbol_map.get(pos) != "λ"
        ):
            accepting_states.add(state_name)

    # print("Estados de aceptacion:")
    # print(accepting_states)

    # Construimos el mapeo de tokens para cada estado de aceptación:
    state_token_mapping = {}
    for state_name, positions in states.items():
        token_dict = {}
        # Usamos la ε-cerradura para asegurarnos de incluir marcadores alcanzables vía λ.
        effective_positions = epsilon_closure(positions, position_symbol_map, followpos)
        # Para cada posición efectiva, si es un marcador, lo agregamos al mapeo de tokens.
        for pos in effective_positions:
            symbol = position_symbol_map.get(pos)
            if symbol and is_marker(symbol):
                token_dict[int(symbol)] = marker_mapping[int(symbol)]
        if token_dict:
            state_token_mapping[state_name] = token_dict

    return states, transitions, accepting_states, state_token_mapping


"""

Esta función se realizó con ayuda de LLMs para poder entender mejor el funcionamiento de la minimización de un AFD

Promt utilizado:

Could you help me with a function that minimizes an AFD using the method of equivalent state partitioning? I need to minimize the AFD that I built from a regular expression. I need to minimize the states, transitions, and accepting states if possible.

"""


def minimize_afd(states, transitions, accepting_states, old_token_actions):
    """
    Minimiza el AFD utilizando el método de partición de estados equivalentes,
    separando los estados de aceptación según su asignación de token.
    """
    # 1. Inicializar particiones

    # Obtener estados no de aceptación
    non_accepting_states = set(states.keys()) - set(accepting_states)

    # Inicializar particiones para estados de aceptación, separándolos por asignación de token.
    # Usaremos el conjunto (frozenset) de pares (marcador, token) como clave.
    accepting_partitions = {}
    for state in accepting_states:
        token_dict = old_token_actions.get(state, {})
        # Creamos una clave inmutable a partir de los pares (marcador, token)
        token_key = frozenset(token_dict.items())
        if token_key not in accepting_partitions:
            accepting_partitions[token_key] = set()
        accepting_partitions[token_key].add(state)

    # La partición P será la unión de las particiones de aceptación (segregadas por token)
    # y los estados no de aceptación (todos en un mismo grupo).
    P = list(accepting_partitions.values())
    if non_accepting_states:
        P.append(non_accepting_states)

    # Inicializar el conjunto de trabajo W como copia de P
    W = P.copy()

    def get_partition(state, partitions):
        for i, group in enumerate(partitions):
            if state in group:
                return i
        return None

    # 2. Refinar particiones
    while W:
        A = W.pop()  # Extraer un grupo de trabajo
        # Para cada símbolo de transición
        for symbol in set(sym for _, sym in transitions.keys()):
            X = {
                state
                for state in states
                if (state, symbol) in transitions and transitions[(state, symbol)] in A
            }
            # Revisar cada grupo Y en P y refinar si es necesario
            for Y in P[:]:
                interseccion = X & Y
                diferencia = Y - X
                if interseccion and diferencia:
                    P.remove(Y)
                    P.append(interseccion)
                    P.append(diferencia)
                    if Y in W:
                        W.remove(Y)
                        W.append(interseccion)
                        W.append(diferencia)
                    else:
                        W.append(
                            interseccion
                            if len(interseccion) <= len(diferencia)
                            else diferencia
                        )

    # 3. Construcción del nuevo AFD minimizado
    new_states = {chr(65 + i): group for i, group in enumerate(P) if group}
    state_mapping = {
        state: new_state for new_state, group in new_states.items() for state in group
    }

    new_transitions = {}
    for (state, symbol), next_state in transitions.items():
        if state in state_mapping and next_state in state_mapping:
            new_transitions[(state_mapping[state], symbol)] = state_mapping[next_state]

    initial_state = "A"  # Estado inicial del AFD original
    new_initial_state = state_mapping[initial_state]

    new_accepting_states = {
        new_state
        for new_state, group in new_states.items()
        if any(s in accepting_states for s in group)
    }

    # Propagar el mapeo de token para el nuevo AFD minimizado.
    # Dado que en la partición inicial se separaron estados con asignaciones diferentes,
    # cada grupo tendrá un único token (el conjunto de pares será idéntico en todo el grupo).
    new_token_actions = {}
    for new_state, group in new_states.items():
        merged_mapping = {}
        orig_info = {}
        for old_state in group:
            if old_state in old_token_actions:
                mapping_old = old_token_actions[old_state]
                # Fusionamos los pares; dado que en este grupo todos deben ser iguales, podemos tomar cualquiera.
                merged_mapping.update(mapping_old)
                orig_info[old_state] = mapping_old
        if merged_mapping:
            new_token_actions[new_state] = {"merged": merged_mapping, "orig": orig_info}

    return (
        new_states,
        new_transitions,
        new_accepting_states,
        new_initial_state,
        new_token_actions,
    )


# Función para imprimir el AFD
def print_afd(states, transitions, accepting_states):
    print(Fore.CYAN + "\n--- Tabla de Estados - AFD directo ---" + Style.RESET_ALL)
    for state, positions in states.items():
        highlight = Fore.YELLOW if state in accepting_states else ""
        print(f"{highlight}Estado {state}: {sorted(positions)}{Style.RESET_ALL}")

    print(Fore.CYAN + "\n--- Transiciones ---" + Style.RESET_ALL)
    for (state, symbol), next_state in transitions.items():
        highlight = Fore.YELLOW if state in accepting_states else ""
        print(f"{highlight}{state} --({symbol})--> {next_state}{Style.RESET_ALL}")

    if accepting_states:
        print(
            Fore.YELLOW
            + f"\nEstados de aceptación: {', '.join(accepting_states)}"
            + Style.RESET_ALL
        )


# Función para imprimir el AFD minimizado
def print_mini_afd(states, transitions, accepting_states):
    print(Fore.CYAN + "\n--- Tabla de Estados - AFD Minimizado ---" + Style.RESET_ALL)
    for state, positions in states.items():
        highlight = Fore.YELLOW if state in accepting_states else ""
        print(f"{highlight}Estado {state}: {sorted(positions)}{Style.RESET_ALL}")

    print(Fore.CYAN + "\n--- Transiciones ---" + Style.RESET_ALL)
    for (state, symbol), next_state in transitions.items():
        highlight = Fore.YELLOW if state in accepting_states else ""
        print(f"{highlight}{state} --({symbol})--> {next_state}{Style.RESET_ALL}")

    if accepting_states:
        print(
            Fore.YELLOW
            + f"\nEstados de aceptación: {', '.join(accepting_states)}"
            + Style.RESET_ALL
        )


# Función para generar la representación gráfica del AFD en una carpeta específica
def visualize_afd(states, transitions, accepting_states, route):
    """
    Genera la representación gráfica del AFD y la guarda en:
      "./grafos/<route>/direct_AFD/grafo_AFD.png"
    """
    output_dir = os.path.join(".", "grafos", route, "direct_AFD")
    os.makedirs(output_dir, exist_ok=True)

    dot = graphviz.Digraph(format="pdf")
    dot.attr(rankdir="LR")
    dot.attr(size="10,7", ratio="fill", dpi="300")

    for state in states:
        if state in accepting_states:
            dot.node(state, state, shape="doublecircle", color="blue")
        else:
            dot.node(state, state, shape="circle")
    for (state, symbol), next_state in transitions.items():
        dot.edge(state, next_state, label=symbol)

    output_path = os.path.join(output_dir, "grafo_AFD")
    dot.render(output_path, view=False)


# Función para generar la representación gráfica del AFD minimizado
def visualize_minimized_afd(
    states, transitions, accepting_states, initial_state, route
):
    """
    Genera la representación gráfica del AFD minimizado y la guarda en:
      "./grafos/<route>/minimize_AFD/grafo_mini_AFD.png"
    """
    output_dir = os.path.join(".", "grafos", route, "minimize_AFD")
    os.makedirs(output_dir, exist_ok=True)

    dot = graphviz.Digraph(format="pdf")
    dot.attr(rankdir="LR")
    dot.attr(size="10,7", ratio="fill", dpi="300")

    for state in states:
        if state in accepting_states:
            dot.node(state, state, shape="doublecircle", color="blue")
        else:
            dot.node(state, state, shape="circle")
    for (state, symbol), next_state in transitions.items():
        dot.edge(state, next_state, label=symbol)

    output_path = os.path.join(output_dir, "grafo_mini_AFD")
    dot.render(output_path, view=False)
