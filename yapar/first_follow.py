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
    # Inicializar el diccionario de conjuntos FOLLOW
    follow = {}
    for nt in grammar:
        follow[nt] = set()
    # EOF al símbolo inicial
    follow[start_symbol].add("$")

    changed = True
    while changed:
        changed = False
        # Para cada lado izquierdo (LHS) y su lista de producciones
        for lhs in grammar:
            productions = grammar[lhs]
            # Para cada producción (RHS)
            for prod in productions:
                n = len(prod)
                for i in range(n):
                    B = prod[i]
                    # Solo si B es no terminal
                    if B in grammar:
                        # Construir beta (los símbolos después de B)
                        beta = []
                        j = i + 1
                        while j < n:
                            beta.append(prod[j])
                            j += 1
                        # Calcular FIRST(beta)
                        first_beta = set()
                        if len(beta) == 0:
                            # Si beta es vacío, usar FOLLOW(lhs)
                            for sym in follow[lhs]:
                                first_beta.add(sym)
                        else:
                            # Lógica para calcular FIRST(beta)
                            vacio = True
                            for s in beta:
                                if s in grammar:
                                    for fs in first[s]:
                                        if fs != "λ":
                                            first_beta.add(fs)
                                    if "λ" in first[s]:
                                        continue
                                    else:
                                        vacio = False
                                        break
                                else:
                                    # Terminal
                                    first_beta.add(s)
                                    vacio = False
                                    break
                            if vacio:
                                for sym in follow[lhs]:
                                    first_beta.add(sym)
                        # Agregar a FOLLOW(B) todos los símbolos de first_beta
                        before = len(follow[B])
                        for x in first_beta:
                            follow[B].add(x)
                        if len(follow[B]) > before:
                            changed = True
    return follow
