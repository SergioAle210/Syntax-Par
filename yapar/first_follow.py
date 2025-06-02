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
def compute_follow(grammar, first, start_symbol):
    follow = {nt: set() for nt in grammar}
    follow[start_symbol].add("$")  # EOF al símbolo inicial

    changed = True
    while changed:
        changed = False
        for lhs, productions in grammar.items():
            for production in productions:
                for i, B in enumerate(production):
                    if B not in grammar:  # Sólo procesamos no terminales
                        continue
                    beta = production[i+1:]
                    # FIRST(beta) - {λ} a FOLLOW(B)
                    first_beta = set()
                    for symbol in beta:
                        if symbol in grammar:
                            first_beta.update(first[symbol] - {"λ"})
                            if "λ" in first[symbol]:
                                continue
                            else:
                                break
                        else:
                            first_beta.add(symbol)
                            break
                    else:
                        # Si todos en beta pueden derivar λ, añade FOLLOW(lhs)
                        first_beta.update(follow[lhs])
                    # Añadir a FOLLOW(B)
                    before = len(follow[B])
                    follow[B].update(first_beta)
                    if len(follow[B]) > before:
                        changed = True
    return follow


# Cálculo de los conjuntos FIRST y FOLLOW para la gramática dada.
first = compute_first(grammar)
follow = compute_follow(grammar, first, "E")

