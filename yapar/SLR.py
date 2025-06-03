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
                # Buscar el índice de la producción exactamente igual a (lhs, rhs)
                for j in range(len(enumerated_productions)):
                    prod = enumerated_productions[j]
                    p_idx = prod[0]
                    p_lhs = prod[1]
                    p_rhs = prod[2]
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
                    # Si ambos coinciden, encontramos el índice
                    if lhs_igual and rhs_igual:
                        prod_idx = p_idx
                        break
                if prod_idx == -1:
                    continue

                # Producción aumentada
                if prod_idx == 0:
                    action_table[i]["$"] = "acc"
                else:
                    # Recorrer el conjunto FOLLOW
                    follow_set = []
                    for sym in follow_sets.get(lhs, set()):
                        follow_set.append(sym)
                    for j in range(len(follow_set)):
                        symbol = follow_set[j]
                        # Verificar si symbol está en terminals
                        es_terminal = False
                        for k in range(len(terminals)):
                            if terminals[k] == symbol:
                                es_terminal = True
                                break
                        if es_terminal:
                            terminal = symbol
                        else:
                            # Buscar si está en el token_map y si su valor está en terminals
                            encontrado = False
                            if symbol in token_map:
                                mapped = token_map[symbol]
                                for k in range(len(terminals)):
                                    if terminals[k] == mapped:
                                        encontrado = True
                                        terminal = mapped
                                        break
                            if not encontrado:
                                continue
                        # Si ya hay acción y es diferente, lo puedes loggear, pero igual sobrescribe
                        if action_table[i][terminal] is not None and action_table[i][
                            terminal
                        ] != ("r" + str(prod_idx)):
                            # No uses print si vas a guardar logs en archivo, solo agrégalo donde corresponda
                            pass
                        action_table[i][terminal] = "r" + str(prod_idx)

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


def enumerate_productions(productions, start_symbol):
    prod_list = []
    idx = 0
    for head in productions:
        for body in productions[head]:
            prod_list.append((idx, head, body))
            idx += 1
    return prod_list
