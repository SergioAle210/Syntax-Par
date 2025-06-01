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
    follow = {nonterm: set() for nonterm in grammar}
    follow[start_symbol].add("$")

    changed = True
    while changed:
        changed = False
        for left in grammar:
            for production in grammar[left]:
                for i, symbol in enumerate(production):
                    # Solo se procesa si el símbolo es un no terminal
                    if symbol in grammar:
                        beta = production[i + 1 :]
                        # --- Regla 2: Si beta no es vacío, añade FIRST(beta) (sin λ) a FOLLOW(symbol) ---
                        first_beta = set()
                        for b in beta:
                            if b not in grammar:  # terminal
                                first_beta.add(b)
                                break
                            else:  # no terminal
                                first_beta.update(first[b] - {"λ"})
                                if "λ" in first[b]:
                                    continue
                                else:
                                    break
                        before = len(follow[symbol])
                        follow[symbol].update(first_beta)
                        if len(follow[symbol]) > before:
                            changed = True

                        # --- Regla 3: Si beta es vacío o puede derivar λ, añade FOLLOW(left) a FOLLOW(symbol) ---
                        if (
                            not beta or
                            all((b in grammar and "λ" in first[b]) or (b not in grammar and b == "λ") for b in beta)
                        ):
                            before = len(follow[symbol])
                            follow[symbol].update(follow[left])
                            if len(follow[symbol]) > before:
                                changed = True
    return follow


# Cálculo de los conjuntos FIRST y FOLLOW para la gramática dada.
first = compute_first(grammar)
follow = compute_follow(grammar, first, "E")

