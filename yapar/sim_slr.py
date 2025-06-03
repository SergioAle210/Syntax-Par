def simulate_slr_parser(action_table, goto_table, productions_enum, token_stream, start_symbol):
    """
    Simula el análisis SLR/LR con la tabla construida usando un generador de tokens.
    Recibe:
      - token_stream: generador o iterador de (token, lexema)
      - start_symbol: símbolo inicial original
    Retorna:
      - accepted (True/False)
      - lista de acciones realizadas
      - mensaje de error detallado si ocurre
    """
    stack = [0]
    actions = []
    tokens = iter(token_stream)

    def next_valid_token():
        while True:
            try:
                tok, lex = next(tokens)
                if tok != 'ws':
                    return tok, lex
                else:
                    print(f"[DEBUG] Ignorando token: {tok} (lexema: '{lex}')")
            except StopIteration:
                return '$', ''

    lookahead_token, lookahead_lexeme = next_valid_token()
    print(f">>> [DEBUG] Primer token: {lookahead_token} (lexema: '{lookahead_lexeme}')")

    while True:
        state = stack[-1]
        current_token = lookahead_token if lookahead_token is not None else '$'
        action = action_table.get(state, {}).get(current_token, None)

        print(f"[DEBUG] Antes del ciclo de reducciones: state={state}, token={current_token}, stack={stack}")
        print(">> DEBUG: Entrando a ciclo de reducción global")

        while action is not None and action.startswith("r"):
            prod_num = int(action[1:])
            _, lhs, rhs = productions_enum[prod_num]
            actions.append(("reduce", state, f"{lhs} → {' '.join(rhs) if rhs else 'λ'}"))
            print(f"\n[DEBUG] Reduciendo {lhs} → {' '.join(rhs)} en estado {state} con token {current_token}")
            for _ in range(len(rhs) * 2):
                stack.pop()
            prev_state = stack[-1]
            stack.append(lhs)
            if lhs not in goto_table[prev_state]:
                print(f"[ERROR] No hay GOTO({prev_state}, {lhs})")
                return False, actions, f"Error: GOTO no definido para ({prev_state}, {lhs})"
            goto_state = goto_table[prev_state][lhs]
            stack.append(goto_state)
            state = goto_state
            print("  Stack después del push:", stack)

            for i, v in enumerate(stack):
                if i % 2 == 0 and not isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser estado, pero es {v}")
                if i % 2 == 1 and isinstance(v, int):
                    print(f"[INVARIANT ERROR] Posición {i} debería ser símbolo, pero es {v}")

            action = action_table.get(state, {}).get(current_token, None)

        # --- Aceptación manual si llegamos al símbolo inicial aumentado ---
        # --- Aceptación manual robusta ---
        if lookahead_token == '$':
            for (idx, lhs, rhs) in productions_enum:
                if lhs.endswith("'") and rhs == [start_symbol]:
                    # Caso típico: stack es [0, 'S', 7]
                    if stack == [0, rhs[0], goto_table[0][rhs[0]]]:
                        actions.append(("accept", stack[-1], '$'))
                        return True, actions, None


        if action is None:
            print(f"[ERROR] Sintáctico en estado {state} con token '{current_token}'")
            mensaje = f"Error sintáctico en estado {state} con token '{current_token}'. Intentando recuperación..."
            sync_tokens = {'SEMICOLON', '$', 'ID', 'LPAREN'}
            actions.append(("error", state, current_token, mensaje))

            while lookahead_token not in sync_tokens:
                print(f"[RECOVERY] Descartando token: {lookahead_token}")
                lookahead_token, lookahead_lexeme = next_valid_token()
                print(f">>> [DEBUG] Nuevo token: {lookahead_token} (lexema: '{lookahead_lexeme}')")

            recovered = False
            for i in reversed(range(0, len(stack), 2)):
                recovery_state = stack[i]
                posibles_acciones = action_table.get(recovery_state, {})
                if (lookahead_token in posibles_acciones and
                    posibles_acciones[lookahead_token] and
                    not posibles_acciones[lookahead_token].startswith('r')):
                    print(f"[RECOVERY] Saltando a estado {recovery_state} con token {lookahead_token}")
                    stack = stack[:i + 1]
                    recovered = True
                    break

            if not recovered or lookahead_token == '$':
                actions.append(("fatal", state, lookahead_token, "No se pudo recuperar el análisis"))
                return False, actions, "Error fatal: No se pudo recuperar del error sintáctico"

            lookahead_token, lookahead_lexeme = next_valid_token()
            print(f">>> [DEBUG] Nuevo token: {lookahead_token} (lexema: '{lookahead_lexeme}')")
            continue

        elif action == "acc":
            actions.append(("accept", state, current_token))
            return True, actions, None

        elif action.startswith("s"):
            next_state = int(action[1:])
            actions.append(("shift", state, current_token, next_state))
            stack.append(current_token)
            stack.append(next_state)
            print(f"[DEBUG] Shift: stack después de shift: {stack}")

            lookahead_token, lookahead_lexeme = next_valid_token()
            print(f">>> [DEBUG] Nuevo token: {lookahead_token} (lexema: '{lookahead_lexeme}')")
            continue
