import os
import json
import pickle


def compute_slr_table(
    grammar,
    first_sets,
    follow_sets,
    lr0_states,
    lr0_transitions,
    enumerated_productions,
    terminals,
    nonterminals,
    token_map,
):
    action_table = {}
    goto_table = {}

    for i in range(len(lr0_states)):
        action_table[i] = {}
        for t in terminals:
            action_table[i][t] = None
        action_table[i]["$"] = None
        goto_table[i] = {}
        for nt in nonterminals:
            goto_table[i][nt] = None

    for i in range(len(lr0_states)):
        state = lr0_states[i]
        for item in state:
            lhs = item[0]
            rhs = item[1]
            dot_pos = item[2]

            # --- SHIFT ---
            if dot_pos < len(rhs):
                symbol = rhs[dot_pos]

                # ─── traducir con token_map si hace falta ───
                if symbol not in terminals and symbol in token_map:
                    symbol_mapped = token_map[symbol]  # '+' → 'PLUS'
                else:
                    symbol_mapped = symbol

                if symbol_mapped in terminals:
                    next_state_idx = lr0_transitions.get((i, symbol), None)
                    if next_state_idx is not None:
                        prev = action_table[i][symbol_mapped]
                        new = "s" + str(next_state_idx)
                        if prev and prev != new:
                            print("Conflicto Shift en estado", i, "símbolo", symbol)
                        action_table[i][symbol_mapped] = new

            # --- REDUCE ---
            elif dot_pos == len(rhs):
                prod_idx = -1

                # ── 1. Buscar la producción correspondiente en enumerated_productions ──
                for j in range(len(enumerated_productions)):
                    p_idx, p_lhs, p_rhs = enumerated_productions[j]

                    # Comparar lhs
                    lhs_igual = True
                    if len(p_lhs) != len(lhs):
                        lhs_igual = False
                    else:
                        for k in range(len(lhs)):
                            if p_lhs[k] != lhs[k]:
                                lhs_igual = False
                                break

                    # Comparar rhs
                    rhs_igual = True
                    if len(p_rhs) != len(rhs):
                        rhs_igual = False
                    else:
                        for k in range(len(rhs)):
                            if p_rhs[k] != rhs[k]:
                                rhs_igual = False
                                break

                    if lhs_igual and rhs_igual:
                        prod_idx = p_idx
                        break

                if prod_idx == -1:
                    continue  # No encontramos la producción; pasamos a la siguiente

                # ── 2. Producción aumentada (aceptación) ──
                if prod_idx == 0:
                    action_table[i]["$"] = "acc"
                else:
                    # ── 3. Para cada símbolo en FOLLOW(lhs) añadimos la reducción rX ──
                    follow_set = list(follow_sets.get(lhs, set()))

                    for j in range(len(follow_set)):
                        symbol = follow_set[j]

                        # --- Caso especial: '$' debe considerarse terminal válido ---
                        if symbol == "$":
                            terminal = "$"
                        else:
                            # ¿Está el símbolo directamente en terminals?
                            es_terminal = False
                            for k in range(len(terminals)):
                                if terminals[k] == symbol:
                                    es_terminal = True
                                    break

                            if es_terminal:
                                terminal = symbol
                            else:
                                # Intentar mapear usando token_map
                                encontrado = False
                                if symbol in token_map:
                                    mapped = token_map[symbol]
                                    for k in range(len(terminals)):
                                        if terminals[k] == mapped:
                                            encontrado = True
                                            terminal = mapped
                                            break
                                if not encontrado:
                                    continue  # No es terminal; seguir con el siguiente símbolo

                        # --- 4. Registrar la acción de reducción r<prod_idx> ---
                        nueva_accion = "r" + str(prod_idx)
                        vieja_accion = action_table[i][terminal]

                        if vieja_accion is not None and vieja_accion != nueva_accion:
                            # Si quieres, registra el conflicto en tu log; aquí solo sobrescribimos
                            pass

                        action_table[i][terminal] = nueva_accion

        # GOTO
        for nt in nonterminals:
            key = (i, nt)
            if key in lr0_transitions:
                next_state_idx = lr0_transitions[key]
                if next_state_idx is not None:
                    goto_table[i][nt] = next_state_idx

    return action_table, goto_table


def save_slr_table(action_table, goto_table, filename="output/slr_table"):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename + "_action.json", "w", encoding="utf-8") as f:
        json.dump(action_table, f, indent=4)
    with open(filename + "_goto.json", "w", encoding="utf-8") as f:
        json.dump(goto_table, f, indent=4)
    with open(filename + ".pickle", "wb") as f:
        pickle.dump({"action": action_table, "goto": goto_table}, f)


def enumerate_productions(productions: dict, start_symbol: str):
    """
    Devuelve la lista [(idx, lhs, rhs)…] asegurando que la producción
    aumentada (start_symbol) quede con índice 0.
    """
    prod_list = []
    idx = 0

    # 1. producción aumentada primero
    for body in productions[start_symbol]:
        prod_list.append((idx, start_symbol, body))
        idx += 1

    # 2. el resto, en el orden original
    for head in productions:
        if head == start_symbol:
            continue
        for body in productions[head]:
            prod_list.append((idx, head, body))
            idx += 1

    return prod_list
