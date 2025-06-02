import os
import json
import pickle


def compute_slr_table(grammar, first_sets, follow_sets, lr0_states, lr0_transitions, enumerated_productions, terminals, nonterminals):
    """
    Construye la tabla de análisis sintáctico SLR(1).

    Args:
        grammar (Grammar): Objeto Grammar con las producciones.
        first_sets (dict): Diccionario de conjuntos FIRST.
        follow_sets (dict): Diccionario de conjuntos FOLLOW.
        lr0_states (list): Lista de estados LR(0).
        lr0_transitions (dict): Diccionario de transiciones LR(0).
        enumerated_productions (list): Lista de producciones enumeradas (idx, lhs, rhs).
        terminals (list): Lista de símbolos terminales.
        nonterminals (list): Lista de símbolos no terminales.

    Returns:
        tuple: Una tupla que contiene (action_table, goto_table).
    """
    action_table = {}
    goto_table = {}

    # Inicializar tablas
    for i in range(len(lr0_states)):
        action_table[i] = {t: None for t in terminals + ['$']}
        goto_table[i] = {nt: None for nt in nonterminals}

    # Llenar tablas
    for i, state in enumerate(lr0_states):
        for item in state:
            lhs, rhs, dot_pos = item
            # Regla 1: Shift
            if dot_pos < len(rhs) and rhs[dot_pos] in terminals:
                symbol = rhs[dot_pos]
                next_state_idx = lr0_transitions.get((i, symbol))
                if next_state_idx is not None:
                    if action_table[i][symbol] is not None and action_table[i][symbol] != f"s{next_state_idx}":
                        print(f"Conflicto Shift-Shift o Shift-Reduce en estado {i}, símbolo {symbol}")
                    action_table[i][symbol] = f"s{next_state_idx}"
            # Regla 2: Reduce
            elif dot_pos == len(rhs):
                # Encontrar el índice de la producción original
                prod_idx = -1
                for p_idx, p_lhs, p_rhs in enumerated_productions:
                    if p_lhs == lhs and tuple(p_rhs) == tuple(rhs):
                        prod_idx = p_idx
                        break
                
                if prod_idx == -1:
                    # Esto no debería pasar si enumerated_productions está bien construida
                    continue

                # Si es la producción aumentada S' -> S., aceptar
                                                # Si es la producción aumentada S' -> S, aceptar
                if prod_idx == 0:
                    action_table[i]['$'] = 'acc'




                else:
                    # Para cada terminal 'a' en FOLLOW(lhs)
                    for terminal in follow_sets.get(lhs, set()):
                        if terminal not in action_table[i]:
                            continue  # Evitar error si terminal no es parte de la tabla

                        if action_table[i][terminal] is not None and action_table[i][terminal] != f"r{prod_idx}":
                            print(f"Conflicto Reduce-Reduce o Shift-Reduce en estado {i}, símbolo {terminal}")
                        action_table[i][terminal] = f"r{prod_idx}"



        # Regla 3: GOTO
        for nonterminal in nonterminals:
            next_state_idx = lr0_transitions.get((i, nonterminal))
            if next_state_idx is not None:
                goto_table[i][nonterminal] = next_state_idx

    return action_table, goto_table

def save_slr_table(action_table, goto_table, filename="output/slr_table"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Guardar ACTION table en JSON
    with open(f"{filename}_action.json", 'w', encoding='utf-8') as f:
        json.dump(action_table, f, indent=4)
    # Guardar GOTO table en JSON
    with open(f"{filename}_goto.json", 'w', encoding='utf-8') as f:
        json.dump(goto_table, f, indent=4)
    # Guardar ambas en un solo archivo pickle
    with open(f"{filename}.pickle", 'wb') as f:
        pickle.dump({'action': action_table, 'goto': goto_table}, f)


def enumerate_productions(productions, start_symbol):
    """
    Devuelve una lista de tuplas (lhs, rhs) donde:
      - lhs es el lado izquierdo (no terminal, str)
      - rhs es la lista de símbolos del lado derecho (list of str)
    El índice de cada tupla es su número de producción.
    La primera producción es la aumentada: S' -> S
    """
    prod_list = []
    for head in productions:
        for body in productions[head]:
            prod_list.append((head, body))
    return prod_list
