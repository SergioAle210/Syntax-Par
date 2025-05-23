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
    # Se inicializa FIRST como un diccionario, asignando a cada no terminal un conjunto vacío.
    first = {nonterm: set() for nonterm in grammar}

    # Función interna para determinar si un símbolo es terminal.
    # Un símbolo se considera terminal si no está definido en la gramática o es la cadena vacía "λ".
    def is_terminal(symbol):
        return symbol not in grammar or symbol == "λ"

    # Se utiliza un bucle que se repite hasta que no haya más cambios en los conjuntos FIRST.
    changed = True
    while changed:
        changed = False
        # Para cada no terminal, se evalúan todas sus producciones.
        for nonterm in grammar:
            for production in grammar[nonterm]:
                # Si la producción es únicamente ["λ"], se agrega "λ" al FIRST del no terminal.
                if production == ["λ"]:
                    if "λ" not in first[nonterm]:
                        first[nonterm].add("λ")
                        changed = True
                    continue  # Se pasa a la siguiente producción.
                # Se recorre la producción símbolo a símbolo.
                for i, symbol in enumerate(production):
                    if is_terminal(symbol):
                        # Si el símbolo es terminal, se agrega directamente al conjunto FIRST.
                        if symbol not in first[nonterm]:
                            first[nonterm].add(symbol)
                            changed = True
                        break  # Como se encontró un terminal, se finaliza la evaluación de esta producción.
                    else:
                        # Si el símbolo es no terminal, se agrega FIRST(symbol) (sin incluir "λ") al FIRST del no terminal.
                        before = len(first[nonterm])
                        first[nonterm].update(first[symbol] - {"λ"})
                        if len(first[nonterm]) > before:
                            changed = True
                        # Si FIRST(symbol) contiene "λ", se debe continuar evaluando el siguiente símbolo
                        # para ver si también puede generar un terminal al inicio.
                        if "λ" in first[symbol]:
                            # Si éste es el último símbolo de la producción y puede ser λ, se agrega "λ".
                            if i == len(production) - 1:
                                if "λ" not in first[nonterm]:
                                    first[nonterm].add("λ")
                                    changed = True
                            # Se sigue evaluando la producción.
                            continue
                        else:
                            # Si no se puede derivar "λ", se termina la evaluación de esta producción.
                            break
    return first


# Función para calcular el conjunto FOLLOW de cada no terminal.
# FOLLOW(A) es el conjunto de símbolos terminales que pueden aparecer inmediatamente a la derecha de A en alguna derivación.
def compute_follow(grammar, first, start_symbol):
    # Se inicializa FOLLOW como un diccionario con conjuntos vacíos para cada no terminal.
    follow = {nonterm: set() for nonterm in grammar}
    # Regla 1: El símbolo de inicio siempre incluye "$" en su FOLLOW.
    follow[start_symbol].add("$")

    # Se itera hasta que no se produzcan cambios en ningún conjunto FOLLOW.
    changed = True
    while changed:
        changed = False
        # Se recorren todas las producciones: para cada producción B -> α,
        # se analiza cada aparición del no terminal (llamémoslo A) en α.
        for left in grammar:
            for production in grammar[left]:
                for i, symbol in enumerate(production):
                    # Solo se procesa si el símbolo es un no terminal (y no es "λ").
                    if symbol in grammar and symbol != "λ":
                        # beta es la secuencia de símbolos que sigue a A en la producción.
                        beta = production[i + 1 :]
                        # Regla 2: Si beta no es vacío, se añade a FOLLOW(A) todo el FIRST(beta) (sin incluir "λ").
                        first_beta = set()
                        for b in beta:
                            if (
                                b not in grammar
                            ):  # Si b es terminal, se agrega y se termina el bucle.
                                first_beta.add(b)
                                break
                            else:
                                # Si b es no terminal, se agrega FIRST(b) sin "λ".
                                first_beta.update(first[b] - {"λ"})
                                # Si b puede generar λ, se evalúa el siguiente símbolo de beta.
                                if "λ" in first[b]:
                                    continue
                                else:
                                    break
                        # Se actualiza el FOLLOW del símbolo con los nuevos elementos obtenidos.
                        before = len(follow[symbol])
                        follow[symbol].update(first_beta)
                        if len(follow[symbol]) > before:
                            changed = True

                        # Regla 3: Si beta es vacío o beta puede derivar la cadena vacía (=>* λ),
                        # se añade el FOLLOW del lado izquierdo (B) a FOLLOW(A).
                        if not beta or (
                            beta and all(b in grammar and "λ" in first[b] for b in beta)
                        ):
                            before = len(follow[symbol])
                            follow[symbol].update(follow[left])
                            if len(follow[symbol]) > before:
                                changed = True
    return follow


# Cálculo de los conjuntos FIRST y FOLLOW para la gramática dada.
first = compute_first(grammar)
follow = compute_follow(grammar, first, "E")

# Impresión de los resultados.
print("Conjuntos FIRST:")
for nonterm in first:
    print(f"{nonterm}: {first[nonterm]}")

print("\nConjuntos FOLLOW:")
for nonterm in follow:
    print(f"{nonterm}: {follow[nonterm]}")
