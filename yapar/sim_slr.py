def simulate_slr_parser(action_table, goto_table, productions_enum, token_stream):
    """
    Simula el análisis SLR/LR con la tabla construida usando un generador de tokens.
    Recibe:
      - token_stream: generador o iterador de (token, lexema)
    Retorna:
      - accepted (True/False)
      - lista de acciones realizadas
      - mensaje de error detallado si ocurre
    """
    stack = [0]  # Stack de estados y símbolos
    actions = []
    tokens = iter(token_stream)
    lookahead_token = None  # El token que está viendo el parser

    # Obtenemos el primer token del stream
    try:
        lookahead_token, _ = next(tokens)
    except StopIteration:
        lookahead_token = '$'  # Usamos $ como fin de entrada si no hay nada

    while True:
        state = stack[-1]
        current_token = lookahead_token if lookahead_token is not None else '$'

        action = action_table.get(state, {}).get(current_token, None)

        # Debug: print before reduction cycle
        print(f"[DEBUG] Antes del ciclo de reducciones: state={state}, token={current_token}, stack={stack}")

        # Si hay múltiples reducciones, sigue reduciendo antes de intentar shift
        while action is not None and action.startswith("r"):
            prod_num = int(action[1:])
            _, lhs, rhs = productions_enum[prod_num]
            actions.append(("reduce", state, f"{lhs} → {' '.join(rhs) if rhs else 'λ'}"))
            # Debug de reduce
            print(f"\n[DEBUG] Reduciendo {lhs} → {' '.join(rhs)} en estado {state} con token {current_token}")
            for _ in range(len(rhs) * 2):
                stack.pop()
            print("  Stack después del pop:", stack)
            state = stack[-1]
            stack.append(lhs)
            goto_state = goto_table[state][lhs]
            print(f"  Hago GOTO({state}, '{lhs}') = {goto_state}")
            stack.append(goto_state)
            print("  Stack después del push:", stack)
            # Invariant check: states at even, symbols at odd positions
            for i, v in enumerate(stack):
                if i % 2 == 0 and not isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser estado, pero es {v}")
                if i % 2 == 1 and isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser símbolo, pero es {v}")
            state = stack[-1]
            action = action_table.get(state, {}).get(current_token, None)

        if action is None:
            print(f"[DEBUG] Stack antes del error: {stack}")
            print(f"[DEBUG] Estado actual: {state}, Token actual: {current_token}")
            print("[DEBUG] Acción esperada según tabla:", action_table.get(state, {}))
            mensaje = (
                f"Error sintáctico en estado {state} con token '{current_token}'."
            )
            posibles = list(action_table.get(state, {}).keys())
            if posibles:
                mensaje += f" Esperaba uno de: {', '.join(map(str, posibles))}."
            actions.append(("error", state, current_token, mensaje))
            return False, actions, mensaje

        elif action == "acc":
            actions.append(("accept", state, current_token))
            return True, actions, None

        elif action.startswith("s"):  # Shift
            next_state = int(action[1:])
            actions.append(("shift", state, current_token, next_state))
            stack.append(current_token)
            stack.append(next_state)
            print(f"[DEBUG] Shift: stack después de shift: {stack}")
            # Invariant check: states at even, symbols at odd positions
            for i, v in enumerate(stack):
                if i % 2 == 0 and not isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser estado, pero es {v}")
                if i % 2 == 1 and isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser símbolo, pero es {v}")
            # Consumimos el siguiente token del generador
            try:
                lookahead_token, _ = next(tokens)
            except StopIteration:
                lookahead_token = '$'

        else:
            mensaje = (
                f"Error sintáctico inesperado en estado {state} con token '{current_token}', acción '{action}'."
            )
            actions.append(("error", state, current_token, mensaje))
            return False, actions, mensaje
