def str_startswith(cadena: str, prefijo: str) -> bool:
    """Equivalente a str.startswith sin usar el método incorporado."""
    if len(prefijo) > len(cadena):
        return False
    for i in range(len(prefijo)):
        if cadena[i] != prefijo[i]:
            return False
    return True


def str_endswith(cadena: str, sufijo: str) -> bool:
    """Equivalente a str.endswith sin usar el método incorporado."""
    if len(sufijo) > len(cadena):
        return False
    for i in range(1, len(sufijo) + 1):
        if cadena[-i] != sufijo[-i]:
            return False
    return True


def simulate_slr_parser(
    action_table: dict,
    goto_table: dict,
    productions_enum: list[tuple[int, str, list[str]]],
    token_stream,
    start_symbol: str,
):
    """
    Ejecuta un parser SLR(1) a partir de sus tablas ACTION/GOTO.

    Parámetros
    ----------
    action_table : dict
        Tabla ACTION[state][token] = acción ("sX", "rY", "acc", None)
    goto_table : dict
        Tabla GOTO[state][NonTerminal] = next_state
    productions_enum : list[(idx, lhs, rhs)]
        Producciones enumeradas, donde rhs es lista de símbolos (puede ser [])
    token_stream : generador
        Produce tuplas (token, lexema) ya filtradas de espacios
    start_symbol : str
        Símbolo inicial original (no el aumentado)

    Retorna
    -------
    accepted : bool
    acciones : list
        Tuplas con la traza de acciones ejecutadas
    error_msg : str | None
        Descripción del fallo si ocurre
    """

    # Pila LR: [estado0, simbolo1, estado1, simbolo2, estado2, ...]
    stack = [0]
    actions_log = []
    tokens = iter(token_stream)

    # Función interna para consumir el próximo token significativo
    def next_valid_token():
        skip = {"ws", "WHITESPACE", "WS", "TAB", "ENTER"}
        while True:
            try:
                tok, lex = next(tokens)
                if tok not in skip:
                    return tok, lex
            except StopIteration:
                return "$", ""

    lookahead_token, lookahead_lexeme = next_valid_token()
    print(f"[DEBUG] Primer token: {lookahead_token} ('{lookahead_lexeme}')")

    # Bucle principal LR
    while True:
        state = stack[-1]
        current_token = lookahead_token or "$"
        action = action_table.get(state, {}).get(current_token)

        while action and str_startswith(action, "r"):
            prod_num = int(action[1:])  # "r3" → 3
            _, lhs, rhs = productions_enum[prod_num]

            actions_log.append(
                ("reduce", state, f"{lhs} → {' '.join(rhs) if rhs else 'λ'}")
            )

            # Pop 2*|rhs| elementos (símbolo + estado) de la pila
            for _ in range(len(rhs) * 2):
                stack.pop()

            prev_state = stack[-1]
            stack.append(lhs)
            goto_state = goto_table[prev_state][lhs]
            stack.append(goto_state)

            state = goto_state
            action = action_table.get(state, {}).get(current_token)

        # ACEPTACIÓN manual cuando lookahead == '$'
        if lookahead_token == "$":
            for _, lhs, rhs in productions_enum:
                if str_endswith(lhs, "'") and rhs == [start_symbol]:
                    if stack == [0, rhs[0], goto_table[0][rhs[0]]]:
                        actions_log.append(("accept", stack[-1], "$"))
                        return True, actions_log, None

        # MANEJO DE ERRORES
        if action is None:
            mensaje = f"Error sintáctico en estado {state} con token '{current_token}'."
            actions_log.append(("error", state, current_token, mensaje))
            print("[ERROR]", mensaje)

            # Conjunto de sincronización (ampliar según gramática)
            sync_tokens = {"SEMICOLON", "$", "ID", "LPAREN"}

            # Descartar tokens hasta encontrar uno de sincronización
            while lookahead_token not in sync_tokens:
                lookahead_token, lookahead_lexeme = next_valid_token()
                print(
                    f"[RECOVERY] Descartando → {lookahead_token} ('{lookahead_lexeme}')"
                )

            # Intentar buscar estado en la pila que acepte este token
            recovered = False
            for i in range(len(stack) - 1, -1, -2):
                st = stack[i]
                posible = action_table.get(st, {}).get(lookahead_token)
                if posible and not str_startswith(posible, "r"):
                    stack = stack[: i + 1]  # cortar la pila
                    recovered = True
                    break

            if not recovered:
                actions_log.append(("fatal", state, current_token, "No recuperable"))
                return False, actions_log, "Error fatal: no se pudo recuperar."

            # No hacemos shift/reduce todavía; volvemos al while principal
            continue

        # ACEPTACIÓN normal
        if action == "acc":
            actions_log.append(("accept", state, current_token))
            return True, actions_log, None

        # SHIFT
        if str_startswith(action, "s"):
            next_state = int(action[1:])  # "s12" → 12
            actions_log.append(("shift", state, current_token, next_state))

            stack.append(current_token)
            stack.append(next_state)

            lookahead_token, lookahead_lexeme = next_valid_token()
            continue
