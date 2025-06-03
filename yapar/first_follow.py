# Gramática para expresiones aritméticas vistas en clase:
# E  -> T E'
# E' -> + T E' | λ
# T  -> F T'
# T' -> * F T' | λ
# F  -> ( E ) | id

# Definición de la gramática como diccionario.
# Cada clave es un no terminal y su valor es una lista de producciones (cada producción es una lista de símbolos).
grammar = {
    "E": [["T", "E'"]],
    "E'": [["+", "T", "E'"], ["λ"]],
    "T": [["F", "T'"]],
    "T'": [["*", "F", "T'"], ["λ"]],
    "F": [["(", "E", ")"], ["id"]],
}


# Función para calcular el conjunto FIRST de cada no terminal de la gramática.
# FIRST(A) es el conjunto de símbolos terminales que pueden aparecer al inicio de alguna cadena derivada de A.
def compute_first(grammar):
    first = {nonterm: set() for nonterm in grammar}

    def is_terminal(symbol):
        # Un símbolo es terminal si no está en la gramática
        return symbol not in grammar

    changed = True
    while changed:
        changed = False
        for nonterm in grammar:
            for production in grammar[nonterm]:
                # AJUSTE: Si la producción es vacía, tratamos como lambda (ε)
                if production == []:
                    if "λ" not in first[nonterm]:
                        first[nonterm].add("λ")
                        changed = True
                    continue
                # Analizamos cada símbolo de la producción
                for i, symbol in enumerate(production):
                    if is_terminal(symbol):
                        if symbol not in first[nonterm]:
                            first[nonterm].add(symbol)
                            changed = True
                        break  # Si es terminal, paramos aquí
                    else:
                        before = len(first[nonterm])
                        first[nonterm].update(first[symbol] - {"λ"})
                        if len(first[nonterm]) > before:
                            changed = True
                        # Si FIRST(symbol) tiene lambda, seguimos con el siguiente símbolo
                        if "λ" in first[symbol]:
                            if i == len(production) - 1:
                                if "λ" not in first[nonterm]:
                                    first[nonterm].add("λ")
                                    changed = True
                            continue
                        else:
                            break
    return first


# Función para calcular el conjunto FOLLOW de cada no terminal.
# FOLLOW(A) es el conjunto de símbolos terminales que pueden aparecer inmediatamente a la derecha de A en alguna derivación.
def compute_follow(grammar, first, start_symbol, token_map, tokens):
    follow = {nt: set() for nt in grammar}
    follow[start_symbol].add("$")  # EOF al símbolo inicial

    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                for i, B in enumerate(production):
                    if B not in grammar:
                        continue
                    beta = production[i+1:]
                    first_beta = set()
                    for symbol in beta:
                        if symbol not in grammar:
                            # SOLO nombre de token: o por token_map, o si ya está en tokens declarados
                            if symbol in token_map:
                                first_beta.add(token_map[symbol])
                            elif symbol in tokens:
                                first_beta.add(symbol)
                            # Si no, ignoramos (no agregamos el literal nunca)
                            break
                        else:
                            first_beta.update(first[symbol] - {"λ"})
                            if "λ" in first[symbol]:
                                continue
                            else:
                                break
                    else:
                        first_beta.update(follow[lhs])
                    before = len(follow[B])
                    follow[B].update(first_beta)
                    if len(follow[B]) > before:
                        changed = True
    return follow
