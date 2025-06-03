# ===============================
# Seccion 0: Funciones auxiliares
# ===============================


def custom_trim(s: str) -> str:
    """Elimina espacios en blanco (espacios, tabs, saltos de línea) al inicio y final de la cadena."""
    start = 0
    while start < len(s) and s[start] in " \t\n\r":
        start += 1
    end = len(s) - 1
    while end >= start and s[end] in " \t\n\r":
        end -= 1
    if start <= end:
        return s[start : end + 1]
    else:
        return ""


def custom_find(text: str, pattern: str, start: int = 0) -> int:
    """Busca la primera ocurrencia de 'pattern' en 'text' a partir de 'start' (implementación manual)."""
    for i in range(start, len(text) - len(pattern) + 1):
        match = True
        for j in range(len(pattern)):
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            return i
    return -1


def custom_split_lines(text: str) -> list:
    """Separa el texto en líneas usando el carácter de salto de línea, leyendo caracter por caracter."""
    lines = []
    current_line = ""
    for ch in text:
        if ch == "\n":
            lines.append(current_line)
            current_line = ""
        else:
            current_line += ch
    if current_line != "":
        lines.append(current_line)
    return lines


def custom_startswith(s: str, prefix: str, pos: int = 0) -> bool:
    """Verifica si s comienza con prefix a partir de pos, sin usar .startswith."""
    if pos < 0 or pos + len(prefix) > len(s):
        return False
    for i in range(len(prefix)):
        if s[pos + i] != prefix[i]:
            return False
    return True


def is_alnum(ch: str) -> bool:
    """Retorna True si ch es alfanumérico (A-Z, a-z, 0-9) sin usar .isalnum()."""
    o = ord(ch)
    return (48 <= o <= 57) or (65 <= o <= 90) or (97 <= o <= 122)


# ===============================
# Sección 1: Funciones para parsear YALex
# ===============================


def remove_comments_yalex(text: str) -> str:
    r"""
    Elimina todas las ocurrencias de comentarios delimitados por '(*' y '*)'
    (asume que los comentarios no están anidados) leyendo caracter por caracter.
    """
    result = ""
    i = 0
    while i < len(text):
        if text[i] == "(" and (i + 1) < len(text) and text[i + 1] == "*":
            i += 2  # Saltar la secuencia "(*"
            while i < len(text):
                if text[i] == "*" and (i + 1) < len(text) and text[i + 1] == ")":
                    i += 2  # Saltar "*)" y salir del comentario
                    break
                else:
                    i += 1
        else:
            result += text[i]
            i += 1
    return result


def extract_header_and_trailer(text: str) -> (str, str, str):  # type: ignore
    """
    Extrae el bloque {header} al inicio y, opcionalmente, el bloque {trailer} al final.
    Se interpreta de la siguiente manera:
      - Si el texto inicia con '{', se toma lo que esté hasta el primer '}' como header.
      - Se busca (de forma manual) un separador de trailer definido como "\n\n{" y se extrae el trailer
        hasta el último '}'.
    """
    text = custom_trim(text)
    header = ""
    trailer = ""
    i = 0
    if i < len(text) and text[i] == "{":
        i += 1
        header_content = ""
        while i < len(text) and text[i] != "}":
            header_content += text[i]
            i += 1
        header = custom_trim(header_content)
        if i < len(text) and text[i] == "}":
            i += 1
        remaining = custom_trim(text[i:])
    else:
        remaining = text

    # Buscar el separador de trailer: la secuencia "\n\n{"
    sep = "\n\n{"
    sep_index = -1
    for i in range(len(remaining) - len(sep) + 1):
        match = True
        for j in range(len(sep)):
            if remaining[i + j] != sep[j]:
                match = False
                break
        if match:
            sep_index = i
    if sep_index != -1:
        trailer_start = (
            sep_index + 2
        )  # Según la especificación, trailer comienza en sep_index+2
        last_brace = -1
        for i in range(len(remaining)):
            if remaining[i] == "}":
                last_brace = i
        if last_brace != -1 and last_brace > trailer_start:
            trailer = custom_trim(remaining[trailer_start:last_brace])
        remaining = custom_trim(remaining[:sep_index])
    return header, trailer, remaining


def extract_definitions(text: str) -> (dict, str):  # type: ignore
    """
    Extrae las definiciones de la forma 'let ident = regexp' de forma línea por línea
    (usando nuestra función custom_split_lines) y retorna un diccionario con las definiciones
    y el texto sin estas líneas.
    """
    definitions = {}
    lines = custom_split_lines(text)
    new_text = ""
    first_line = True
    for line in lines:
        trimmed = custom_trim(line)
        if len(trimmed) >= 4 and trimmed[:4] == "let ":
            sin_let = trimmed[4:]
            eq_index = custom_find(sin_let, "=")
            if eq_index != -1:
                ident = custom_trim(sin_let[:eq_index])
                regexp = custom_trim(sin_let[eq_index + 1 :])
                if regexp != "":
                    # Si el patrón está entre corchetes
                    if regexp[0] == "[" and regexp[-1] == "]":
                        # Procesar como cadena literal solo si el contenido interno comienza con comillas dobles.
                        # Si comienza con comillas simples, se asume que es un conjunto y se deja sin procesar.
                        inner = custom_trim(regexp[1:-1])
                        if inner != "" and inner[0] == '"':
                            regexp = process_string_literal(regexp)
                        else:
                            # Para conjuntos (por ejemplo, ['A'-'Z''a'-'z']) se deja tal cual,
                            # o se podría llamar a otra función como expand_bracket_ranges.
                            regexp = regexp
                    # Si el patrón comienza con comillas (pero no está entre corchetes)
                    elif regexp[0] == '"' or regexp[0] == "'":
                        regexp = process_string_constant(regexp)
                definitions[ident] = regexp
        else:
            if not first_line:
                new_text += "\n"
            new_text += line
            first_line = False
    return definitions, new_text


def extract_rule(text: str) -> (str, str):  # type: ignore
    """
    Extrae la sección 'rule entrypoint [...] =' de forma manual.
    Retorna el nombre del entrypoint y el cuerpo de la regla.
    """
    idx = custom_find(text, "rule ")
    if idx == -1:
        return "", ""
    end_line = -1
    for i in range(idx, len(text)):
        if text[i] == "\n":
            end_line = i
            break
    if end_line == -1:
        end_line = len(text)
    rule_header = ""
    for i in range(idx, end_line):
        rule_header += text[i]
    parts = []
    current = ""
    for ch in rule_header:
        if ch == " ":
            if current != "":
                parts.append(current)
                current = ""
        else:
            current += ch
    if current != "":
        parts.append(current)
    entrypoint_name = parts[1] if len(parts) > 1 else ""
    rule_body = ""
    for i in range(end_line, len(text)):
        rule_body += text[i]
    rule_body = custom_trim(rule_body)
    return entrypoint_name, rule_body


def process_token_literal(literal: str) -> str:
    """
    Dado un literal delimitado por comillas (simples o dobles),
    elimina las comillas y devuelve la secuencia de valores ASCII de cada carácter,
    separados por un espacio.
    Por ejemplo, '":="' se transforma en "58 61".
    """
    # Verificar que la cadena tenga al menos dos caracteres y comience y termine con el mismo delimitador.
    if len(literal) >= 2 and (
        (literal[0] == '"' and literal[-1] == '"')
        or (literal[0] == "'" and literal[-1] == "'")
    ):
        inner = ""
        i = 1
        while i < len(literal) - 1:
            inner += literal[i]
            i += 1
    else:
        inner = literal
    result = ""
    first = True
    i = 0
    while i < len(inner):
        if first:
            result += str(ord(inner[i]))
            first = False
        else:
            result += " " + str(ord(inner[i]))
        i += 1
    return result


def extract_token_rules(rule_body: str) -> list:
    """
    Separa las alternativas del cuerpo de la regla (usando split_top_level) y extrae,
    para cada alternativa, el bloque de acción (entre '{' y '}') si existe.
    Retorna una lista de tuplas (regexp, action).
    """
    token_rules = []
    alternatives = split_top_level(rule_body)
    for alt in alternatives:
        alt = custom_trim(alt)
        if alt == "":
            continue
        open_brace_index = custom_find(alt, "{")
        if open_brace_index != -1:
            close_brace_index = -1
            for i in range(len(alt) - 1, -1, -1):
                if alt[i] == "}":
                    close_brace_index = i
                    break
            regexp_part = ""
            for i in range(0, open_brace_index):
                regexp_part += alt[i]
            regexp_part = custom_trim(regexp_part)
            # Si la expresión empieza con comillas, se procesa como literal
            if regexp_part and (regexp_part[0] == '"' or regexp_part[0] == "'"):
                regexp_part = process_token_literal(regexp_part)
            action_part = ""
            if close_brace_index != -1:
                for i in range(open_brace_index + 1, close_brace_index):
                    action_part += alt[i]
                action_part = custom_trim(action_part)
                if len(action_part) >= 6 and action_part[:6].lower() == "return":
                    action_part = custom_trim(action_part[6:])
                    if action_part and action_part[0] == ":":
                        action_part = custom_trim(action_part[1:])
            token_rules.append((regexp_part, action_part))
        else:
            token_rules.append((alt, ""))
    return token_rules


def parse_yalex(filepath: str) -> dict:
    """
    Procesa un archivo YALex leyendo caracter por caracter (sin usar métodos como .split, .strip, etc.)
    y retorna un diccionario con:
      - header, trailer, definitions, entrypoint y rules.
    """
    content = ""
    with open(filepath, "r", encoding="utf-8") as f:
        # Leer caracter por caracter
        while True:
            ch = f.read(1)
            if not ch:
                break
            content += ch
    content = remove_comments_yalex(content)
    header, trailer, remaining = extract_header_and_trailer(content)
    definitions, remaining = extract_definitions(remaining)
    entrypoint, rule_body = extract_rule(remaining)
    token_rules = extract_token_rules(rule_body)

    return {
        "header": header,
        "trailer": trailer,
        "definitions": definitions,
        "entrypoint": entrypoint,
        "rules": token_rules,
    }


# ===============================
# Expansión y transformación de expresiones regulares
# ===============================


def char_to_ascii(c: str) -> int:
    """
    Retorna el valor ASCII del carácter c.
    Ejemplo: char_to_ascii('A') --> 65
    """
    return ord(c)


def custom_escape_char(c: str) -> str:
    """
    Retorna la representación en ASCII del carácter c.
    Ejemplo: custom_escape_char('\n') --> "10"
    """
    return str(ord(c))


def convert_char_literals_to_ascii(regex: str) -> str:
    """
    Recorre la expresión regular y reemplaza las literales de caracteres (entre comillas o literales puntuales)
    por su valor ASCII, sin usar funciones como .strip o .find.
    Por ejemplo: "'A'" se reemplaza por "65" y un punto '.' se reemplaza por "46".
    """
    output = ""
    i = 0
    while i < len(regex):
        c = regex[i]
        if c == "'" or c == '"':
            quote_char = c
            i += 1  # Saltar la comilla de apertura
            literal = ""
            # Extraer el contenido hasta la comilla de cierre
            while i < len(regex) and regex[i] != quote_char:
                if regex[i] == "\\" and i + 1 < len(regex):
                    literal += regex[i] + regex[i + 1]
                    i += 2
                else:
                    literal += regex[i]
                    i += 1
            if i < len(regex) and regex[i] == quote_char:
                i += 1  # Saltar la comilla de cierre
            # Decodificar el literal (interpreta secuencias de escape simples)
            if len(literal) >= 1 and literal[0] == "\\" and len(literal) > 1:
                esc = literal[1]
                if esc == "n":
                    decoded = "\n"
                elif esc == "t":
                    decoded = "\t"
                elif esc == "r":
                    decoded = "\r"
                elif esc in ("'", '"', "\\"):
                    decoded = esc
                else:
                    decoded = literal[1]
            else:
                decoded = literal[0] if len(literal) > 0 else ""
            if decoded != "":
                output += str(ord(decoded))
        elif c == ".":  # Si el carácter es un punto, lo convertimos a ASCII (46)
            output += str(ord("."))
            i += 1
        else:
            output += c
            i += 1
    return output


def process_regexp(regex: str) -> str:
    """
    Procesa la expresión regular reemplazando las literales por su valor ASCII.
    """
    processed = convert_char_literals_to_ascii(regex)
    return processed


def expand_regex(expr: str, definitions: dict) -> str:
    """
    Expande en la expresión regular todas las referencias a identificadores definidos en 'definitions'.
    Cada identificador se reemplaza por su patrón entre paréntesis, preservando la precedencia.
    La expansión es recursiva.
    """
    changed = True
    while changed:
        changed = False
        new_expr = ""
        i = 0
        while i < len(expr):
            found = False
            for ident, pattern in definitions.items():
                if custom_startswith(expr, ident, i):
                    # Verificar que la ocurrencia sea token completo:
                    before_ok = (i == 0) or (not is_alnum(expr[i - 1]))
                    after_index = i + len(ident)
                    after_ok = (after_index == len(expr)) or (
                        not is_alnum(expr[after_index])
                    )
                    if before_ok and after_ok:
                        new_expr += "(" + pattern + ")"
                        i += len(ident)
                        changed = True
                        found = True
                        break
            if not found:
                new_expr += expr[i]
                i += 1
        expr = new_expr
    return expr


def escape_token_literals(expr: str) -> str:
    """
    Busca en la expresión subcadenas entre comillas simples.
    Si el contenido es un solo carácter y es un operador especial (por ejemplo, +, *, (, )), se lo escapa.
    """
    result = ""
    i = 0
    while i < len(expr):
        if expr[i] == "'":
            # Buscar manualmente la siguiente comilla simple
            j = -1
            k = i + 1
            while k < len(expr):
                if expr[k] == "'":
                    j = k
                    break
                k += 1
            if j != -1:
                literal = ""
                k = i + 1
                while k < j:
                    literal += expr[k]
                    k += 1
                if len(literal) == 1 and literal in "+*()-/%":
                    result += "\\" + literal
                else:
                    result += literal
                i = j + 1
            else:
                result += expr[i]
                i += 1
        elif expr[i] == '"':
            # Buscar la siguiente comilla doble manualmente
            j = -1
            k = i + 1
            while k < len(expr):
                if expr[k] == '"':
                    j = k
                    break
                k += 1
            if j != -1:
                literal = ""
                k = i + 1
                while k < j:
                    literal += expr[k]
                    k += 1
                if literal != "":
                    transformed = literal[0]
                    for ch in literal[1:]:
                        transformed += "." + ch
                    result += transformed
                else:
                    result += "λ"
                i = j + 1
            else:
                result += expr[i]
                i += 1
        else:
            result += expr[i]
            i += 1
    return result


def custom_escape_str(s: str) -> str:
    """
    Retorna la representación en ASCII del carácter s.
    Si s es una secuencia de escape (por ejemplo, "\t"), la decodifica.
    """
    if len(s) >= 2 and s[0] == "\\":
        esc = s[1]
        if esc == "n":
            return str(ord("\n"))
        elif esc == "t":
            return str(ord("\t"))
        elif esc == "r":
            return str(ord("\r"))
        elif esc in ("'", '"', "\\"):
            return str(ord(esc))
        else:
            return str(ord(s[1]))
    else:
        return str(ord(s))


def expand_bracket_content(content: str) -> str:
    """
    Expande el contenido de un conjunto al estilo YALex.
    Ejemplo: "['0'-'9']" se expande a "(48|49|...|57)" usando el valor ASCII.
    """
    content = custom_trim(content)
    expanded_chars = []
    i = 0
    while i < len(content):
        if content[i] == "'":
            j = custom_find(content, "'", i + 1)
            if j == -1:
                break
            char1 = ""
            k = i + 1
            while k < j:
                char1 += content[k]
                k += 1
            # Verificar si es un rango, ej: 'A'-'Z'
            if j + 1 < len(content) and content[j + 1] == "-" and j + 2 < len(content):
                if content[j + 2] == "'":
                    k = j + 3
                    j2 = custom_find(content, "'", k)
                    if j2 == -1:
                        break
                    char2 = ""
                    while k < j2:
                        char2 += content[k]
                        k += 1
                    for c in range(ord(char1), ord(char2) + 1):
                        expanded_chars.append(custom_escape_str(chr(c)))
                    i = j2 + 1
                    continue
            expanded_chars.append(custom_escape_str(char1))
            i = j + 1
        else:
            i += 1
    # Concatenar los valores con "|" manualmente
    joined = ""
    for idx, val in enumerate(expanded_chars):
        if idx > 0:
            joined += "|"
        joined += val
    return "(" + joined + ")"


def expand_bracket_ranges(s: str) -> str:
    """
    Reemplaza en s las expresiones entre corchetes '[' y ']' por su expansión.
    Si el contenido interno comienza con '^', se utiliza expand_complement_set.
    Si se detecta el patrón: [ ... ]# [ ... ] (con espacios opcionales)
    se invoca expand_set_difference para procesar la diferencia.
    En otro caso se usa la función expand_bracket_content (ya existente).
    """
    result = ""
    i = 0
    while i < len(s):
        if s[i] == "[":
            # Buscar el cierre del primer conjunto
            j = custom_find(s, "]", i + 1)
            if j == -1:
                result += s[i]
                i += 1
            else:
                # Extraer el contenido del primer conjunto
                content_left = ""
                k = i + 1
                while k < j:
                    content_left += s[k]
                    k += 1
                content_left = custom_trim(content_left)
                print(content_left)

                # Ahora, verificar si justo después de este ']' hay espacios, un '#' y luego otro '['.
                temp = ""
                m = j + 1
                while m < len(s) and s[m] in " \t\n\r":
                    temp += s[m]
                    m += 1
                if m < len(s) and s[m] == "#":
                    m += 1
                    while m < len(s) and s[m] in " \t\n\r":
                        m += 1
                    if m < len(s) and s[m] == "[":
                        # Se detecta el patrón [ ... ]# [ ... ]
                        n = custom_find(s, "]", m + 1)
                        if n != -1:
                            # Extraer el contenido del segundo conjunto (opcional, para depuración)
                            content_right = ""
                            p = m + 1
                            while p < n:
                                content_right += s[p]
                                p += 1
                            content_right = custom_trim(content_right)
                            print(content_right)
                            # Combinar la parte completa: desde la primera '[' hasta el cierre del segundo ']'
                            combined = s[i : n + 1]
                            # Llamar a expand_set_difference sobre la cadena combinada
                            expanded = expand_set_difference(combined)
                            result += expanded
                            i = n + 1
                            continue
                        else:
                            # Si no se encuentra el cierre del segundo conjunto, se procesa el primero normalmente
                            if content_left and content_left[0] == "^":
                                expanded = expand_complement_set(content_left)
                            elif custom_find(content_left, "#") != -1:
                                expanded = expand_set_difference(content_left)
                            else:
                                expanded = expand_bracket_content(content_left)
                            result += expanded
                            i = j + 1
                            continue
                    else:
                        # No hay un segundo conjunto; se procesa el primer conjunto normalmente
                        if content_left and content_left[0] == "^":
                            expanded = expand_complement_set(content_left)
                        elif custom_find(content_left, "#") != -1:
                            expanded = expand_set_difference(content_left)
                        else:
                            expanded = expand_bracket_content(content_left)
                        result += expanded
                        i = j + 1
                        continue
                else:
                    # No se detecta diferencia; procesar el primer conjunto
                    if content_left and content_left[0] == "^":
                        expanded = expand_complement_set(content_left)
                    elif custom_find(content_left, "#") != -1:
                        expanded = expand_set_difference(content_left)
                    else:
                        expanded = expand_bracket_content(content_left)
                    result += expanded
                    i = j + 1
        else:
            result += s[i]
            i += 1
    return result


# ===============================
# Sección 2: Funciones para expandir expresiones regulares
# ===============================


def convert_plus_operator(expr: str) -> str:
    """
    Transforma operadores '+' en la forma: X+  -->  X (X)*,
    manteniendo los '+' escapados como literales.
    """

    def get_operand(expr: str, pos: int) -> (str, int):  # type: ignore
        if pos <= 0:
            return "", 0
        if expr[pos - 1] == ")":
            count = 1
            j = pos - 2
            while j >= 0:
                if expr[j] == ")":
                    count += 1
                elif expr[j] == "(":
                    count -= 1
                    if count == 0:
                        break
                j -= 1
            operand = ""
            k = j
            while k < pos:
                operand += expr[k]
                k += 1
            return operand, j
        else:
            return expr[pos - 1 : pos], pos - 1

    output = ""
    i = 0
    while i < len(expr):
        if expr[i] == "+":
            if i > 0 and expr[i - 1] == "\\":
                output += "+"
                i += 1
                continue
            operand, start_index = get_operand(expr, i)
            if operand == "":
                output += "+"
                i += 1
            else:
                output = output[: len(output) - len(operand)]
                transformed = operand + "(" + operand + ")*"
                output += transformed
                i += 1
        else:
            output += expr[i]
            i += 1
    return output


def convert_optional_operator(expr: str) -> str:
    """
    Convierte el operador '?' en su forma: R?  -->  (R|λ),
    dejando los '?' escapados como literales.

    La conversión se realiza detectando el operando inmediatamente anterior al '?':
      - Si el operando es un grupo entre paréntesis: se toma el grupo completo.
      - Si el operando es un conjunto entre corchetes: se toma la subcadena entre '[' y ']'.
      - Si es otro caso, se toma el último carácter.

    Ejemplos:
      "a?"           se transforma a "(a|λ)"
      "(ab)?"        se transforma a "((ab)|λ)"
      "['+''-']?"    se transforma a "(['+''-']|λ)"
    """
    output = ""
    i = 0
    while i < len(expr):
        if expr[i] == "?":
            # Si el '?' está escapado, se deja como literal.
            if i > 0 and expr[i - 1] == "\\":
                output += "?"
                i += 1
                continue

            # Si hay algo previo, determinar el operando a convertir
            if len(output) > 0:
                last_char = output[-1]
                if last_char == ")":
                    # Se asume que el operando es un grupo entre paréntesis.
                    count = 1
                    j = len(output) - 2
                    while j >= 0:
                        if output[j] == ")":
                            count += 1
                        elif output[j] == "(":
                            count -= 1
                            if count == 0:
                                break
                        j -= 1
                    operand = output[j:]
                    output = output[:j]
                    transformed = "(" + operand + "|λ)"
                    output += transformed
                elif last_char == "]":
                    # Se asume que el operando es un conjunto entre corchetes.
                    count = 1
                    j = len(output) - 2
                    while j >= 0:
                        if output[j] == "]":
                            count += 1
                        elif output[j] == "[":
                            count -= 1
                            if count == 0:
                                break
                        j -= 1
                    operand = output[j:]
                    output = output[:j]
                    transformed = "(" + operand + "|λ)"
                    output += transformed
                else:
                    # Caso por defecto: se toma el último carácter.
                    operand = output[-1]
                    output = output[:-1]
                    transformed = "(" + operand + "|λ)"
                    output += transformed
            else:
                # Caso atípico: no hay operando previo; se asume solo la cadena vacía.
                output += "(λ)"
            i += 1
        else:
            output += expr[i]
            i += 1
    return output


def remove_outer_parentheses(expr: str) -> str:
    """
    Elimina recursivamente paréntesis exteriores redundantes.
    """
    if len(expr) >= 2 and expr[0] == "(" and expr[len(expr) - 1] == ")":
        inner = ""
        i = 1
        while i < len(expr) - 1:
            inner += expr[i]
            i += 1
        # Si inner es un literal escapado
        if (
            len(inner) == 2
            and inner[0] == "\\"
            and (inner[1] == "(" or inner[1] == ")")
        ):
            return inner
        count = 0
        i = 0
        redundant = True
        while i < len(expr):
            if expr[i] == "(":
                count += 1
            elif expr[i] == ")":
                count -= 1
            if count == 0 and i < len(expr) - 1:
                redundant = False
                break
            i += 1
        if redundant:
            return remove_outer_parentheses(inner)
    return expr


def split_top_level(expr: str) -> list:
    """
    Divide la expresión en partes separadas por '|' a nivel superior.
    Se omiten los caracteres que están dentro de comillas (simples o dobles) o
    delimitados por los caracteres de control \x01 y \x02 para no interpretar erróneamente
    paréntesis o el propio '|'.
    """
    parts = []
    current = ""
    level = 0
    i = 0
    while i < len(expr):
        if expr[i] == "\\":
            # Añade la secuencia completa sin procesar
            if i + 1 < len(expr):
                current += expr[i] + expr[i + 1]
                i += 2
                continue
            else:
                current += expr[i]
                i += 1
                continue
        elif expr[i] in ("'", '"'):
            # Se encontró una comilla, copiar todo el contenido hasta la comilla de cierre
            quote_char = expr[i]
            current += expr[i]
            i += 1
            while i < len(expr) and expr[i] != quote_char:
                current += expr[i]
                i += 1
            if i < len(expr):
                current += expr[i]  # la comilla de cierre
                i += 1
            continue
        # --- Agregamos manejo de literales protegidos entre \x01 y \x02 ---
        elif expr[i] == "$":
            current += expr[i]
            i += 1
            while i < len(expr) and expr[i] != "$":
                current += expr[i]
                i += 1
            if i < len(expr) and expr[i] == "$":
                current += expr[i]
                i += 1
            continue
        elif expr[i] == "(":
            level += 1
        elif expr[i] == ")":
            level -= 1
        if expr[i] == "|" and level == 0:
            parts.append(current)
            current = ""
        else:
            current += expr[i]
        i += 1
    if current:
        parts.append(current)
    return parts


def simplify_expression(expr: str) -> str:
    """
    Reduce paréntesis redundantes en cada parte de la expresión a nivel superior.
    """
    parts = split_top_level(expr)
    simplified_parts = []
    for part in parts:
        trimmed = custom_trim(part)
        simplified_parts.append(remove_outer_parentheses(trimmed))
    result = ""
    for idx, part in enumerate(simplified_parts):
        if idx > 0:
            result += "|"
        result += part
    return result


def compute_symbol_code(literal_sym: str, token_name: str) -> str:
    """
    Si hay símbolo literal ⇒ devuelve str(ord(símbolo)).
    Si no hay símbolo:
        • WHITESPACE → 'ws'
        • ID         → 'id'
        • en otro caso se devuelve ''.
    """
    if literal_sym:
        return str(ord(literal_sym))

    # convertir token_name a minúsculas sin usar .lower()
    lower = ""
    for ch in token_name:
        if "A" <= ch <= "Z":
            lower += chr(ord(ch) + 32)
        else:
            lower += ch

    if lower == "whitespace":
        return "ws"
    if lower == "id":
        return "id"
    if lower == "number":
        return "number"
    return ""


def attach_markers_to_final_regexp(
    expr: str,
    actions: list,
    symbols: list,
    start_id: int = 1000,
):  # -> (str, dict)
    """
    Adjunta un marcador único a cada alternativa de la expresión regular `expr`
    y genera un diccionario que mapea cada marcador a la tupla
        (símbolo_literal, nombre_token).

    • `actions[i]`  → nombre del token (p. ej. 'PLUS')
    • `symbols[i]` → símbolo literal asociado (p. ej. '+') o '' si no aplica
    """
    parts = split_top_level(expr)
    new_parts = []
    marker_mapping = {}
    current_id = start_id

    for i in range(len(parts)):
        # ─────— saneo de la sub-expresión ─────—
        stripped = custom_trim(parts[i])

        # envolver con paréntesis si contiene |
        has_pipe = False
        for ch in stripped:
            if ch == "|":
                has_pipe = True
                break
        if has_pipe and not (
            len(stripped) > 0
            and stripped[0] == "("
            and stripped[len(stripped) - 1] == ")"
        ):
            stripped = "(" + stripped + ")"

        # añadir el marcador numérico
        new_parts.append(stripped + " " + str(current_id))

        # ─────— preparar acción y símbolo ─────—
        raw_action = actions[i] if i < len(actions) else ""
        # trim manual
        j = 0
        while j < len(raw_action) and raw_action[j] in " \t\n\r":
            j += 1
        k = len(raw_action) - 1
        while k >= 0 and raw_action[k] in " \t\n\r":
            k -= 1
        clean_action = ""
        idx = j
        while idx <= k:
            clean_action += raw_action[idx]
            idx += 1

        # quitar prefijo "return" (sin startswith)
        lowered = ""
        for ch in clean_action:
            if "A" <= ch <= "Z":
                lowered += chr(ord(ch) + 32)
            else:
                lowered += ch
        if len(lowered) >= 6:
            is_ret = True
            word = "return"
            for p in range(6):
                if lowered[p] != word[p]:
                    is_ret = False
                    break
            if is_ret:
                tmp = ""
                for p in range(6, len(clean_action)):
                    tmp += clean_action[p]
                clean_action = tmp

        # normalizar caso especial
        if clean_action == "number":
            clean_action = "ID"

        literal_sym = symbols[i] if i < len(symbols) else ""

        # **** AQUÍ guardamos TUPLA (símbolo, token) ****
        marker_mapping[current_id] = (literal_sym, clean_action)
        current_id += 1

    # reconstruir la expresión con marcadores
    new_expr = ""
    for idx, part in enumerate(new_parts):
        if idx > 0:
            new_expr += "|"
        new_expr += part
    return new_expr, marker_mapping


def process_string_constant(s: str) -> str:
    r"""
    Procesa una cadena que representa una constante tipo cadena (string-character)
    convirtiendo cada carácter (incluyendo las secuencias de escape válidas) a su valor ASCII,
    y genera una expresión regular que representa la unión de dichos valores.

    Por ejemplo:
      '"\\s\\t\\n"' se convierte en "(32|9|10)".
    """
    if s == "":
        return ""
    delim = s[0]
    if delim not in ("'", '"'):
        return s
    ascii_values = ""
    first = True
    i = 1  # Saltar la comilla de apertura
    while i < len(s):
        if s[i] == delim:
            break  # Fin de la cadena literal
        if s[i] == "\\" and i + 1 < len(s):
            next_char = s[i + 1]
            if next_char == "n":
                decoded = "\n"
            elif next_char == "t":
                decoded = "\t"
            elif next_char == "r":
                decoded = "\r"
            elif next_char == "s":
                decoded = " "  # Se interpreta como espacio (ASCII 32)
            elif next_char in ("'", '"', "\\"):
                decoded = next_char
            else:
                decoded = next_char
            value = str(ord(decoded))
            i += 2
        else:
            value = str(ord(s[i]))
            i += 1
        if first:
            ascii_values += value
            first = False
        else:
            ascii_values += "|" + value
    return "(" + ascii_values + ")"


def process_string_literal(s: str) -> str:
    r"""
    Procesa una cadena literal que se encuentra en las definiciones y que está delimitada por corchetes,
    por ejemplo: ["\s\t\n"]. Se remueven los corchetes y se procesa el contenido si está delimitado por comillas dobles.
    Si el contenido interno no comienza con comillas dobles (por ejemplo, en conjuntos), se retorna tal cual.
    """
    s = custom_trim(s)
    if s != "" and s[0] == "[" and s[-1] == "]":
        inner = ""
        i = 1
        while i < len(s) - 1:
            inner += s[i]
            i += 1
        inner = custom_trim(inner)
        if inner != "" and inner[0] == '"':
            return process_string_constant(inner)
        else:
            return inner
    else:
        return process_string_constant(s)


def expand_complement_set(content: str) -> str:
    """
    Procesa el contenido de un conjunto complementario (sin los corchetes)
    Ejemplo: "^'A'-'Z'"
    Se asume que se trabajará en el dominio de caracteres imprimibles (ASCII 32 a 126).
    Devuelve una cadena con la unión (separada por "|") de los códigos que NO están en el conjunto,
    encerrada entre llaves para que sea tratada como literal.
    """
    i = 0
    if i < len(content) and content[i] == "^":
        i += 1
    set_codes = []
    while i < len(content):
        if content[i] == "'":
            j = i + 1
            literal = ""
            while j < len(content) and content[j] != "'":
                literal += content[j]
                j += 1
            if j < len(content) - 2 and content[j + 1] == "-" and content[j + 2] == "'":
                k = j + 3
                literal2 = ""
                while k < len(content) and content[k] != "'":
                    literal2 += content[k]
                    k += 1
                if literal != "" and literal2 != "":
                    start_val = ord(literal[0])
                    end_val = ord(literal2[0])
                    for code in range(start_val, end_val + 1):
                        if code not in set_codes:
                            set_codes.append(code)
                i = k + 1
            else:
                if literal != "":
                    code = ord(literal[0])
                    if code not in set_codes:
                        set_codes.append(code)
                i = j + 1
        else:
            i += 1

    domain = []
    for code in range(32, 127):
        domain.append(code)
    complement = []
    for code in domain:
        found = False
        for c in set_codes:
            if c == code:
                found = True
                break
        if not found:
            complement.append(code)
    result = ""
    first = True
    for code in complement:
        if first:
            result += str(code)
            first = False
        else:
            result += "|" + str(code)
    # Devolver el resultado entre llaves, para tratarlo como un literal
    return "$" + result + "$"


def expand_set_difference(expr: str) -> str:
    """
    Procesa una expresión de la forma:
       regexp1 # regexp2
    donde ambas partes son conjuntos (con corchetes).
    Devuelve la unión (con "|" entre códigos) de los elementos que están en regexp1 pero no en regexp2,
    encerrada entre llaves para que sea tratada como un literal.
    """
    hash_index = -1
    i = 0
    while i < len(expr):
        if expr[i] == "#":
            hash_index = i
            break
        i += 1
    if hash_index == -1:
        return expr

    left_part = ""
    i = 0
    while i < hash_index:
        left_part += expr[i]
        i += 1
    right_part = ""
    i = hash_index + 1
    while i < len(expr):
        right_part += expr[i]
        i += 1

    def remove_brackets(s: str) -> str:
        s = custom_trim(s)
        if len(s) >= 2 and s[0] == "[" and s[-1] == "]":
            result = ""
            i = 1
            while i < len(s) - 1:
                result += s[i]
                i += 1
            return result
        else:
            return s

    left_inner = remove_brackets(left_part)
    right_inner = remove_brackets(right_part)
    set1 = get_bracket_set(left_inner)
    set2 = get_bracket_set(right_inner)
    diff = []
    for code in set1:
        found = False
        for c in set2:
            if c == code:
                found = True
                break
        if not found:
            diff.append(code)
    result = ""
    first = True
    for code in range(32, 127):
        for d in diff:
            if d == code:
                if first:
                    result += str(code)
                    first = False
                else:
                    result += "|" + str(code)
                break
    return "$" + result + "$"


def get_bracket_set(content: str) -> list:
    """
    Dado el contenido interno de un conjunto (por ejemplo, "'0'-'9'" o "'A''B'"),
    devuelve una lista de códigos ASCII correspondientes a los caracteres especificados.
    Se procesa carácter a carácter.
    """
    codes = []
    i = 0
    while i < len(content):
        if content[i] == "'":
            j = i + 1
            literal = ""
            while j < len(content) and content[j] != "'":
                literal += content[j]
                j += 1
            if j < len(content) - 2 and content[j + 1] == "-" and content[j + 2] == "'":
                k = j + 3
                literal2 = ""
                while k < len(content) and content[k] != "'":
                    literal2 += content[k]
                    k += 1
                if literal != "" and literal2 != "":
                    start_val = ord(literal[0])
                    end_val = ord(literal2[0])
                    for code in range(start_val, end_val + 1):
                        if code not in codes:
                            codes.append(code)
                i = k + 1
            else:
                if literal != "":
                    code = ord(literal[0])
                    if code not in codes:
                        codes.append(code)
                i = j + 1
        else:
            i += 1
    return codes


def expand_underscore() -> str:
    """
    Devuelve una cadena que representa la unión de todos los códigos ASCII del 0 al 255,
    separados por '|' y encerrados entre paréntesis.
    Ejemplo: "(0|1|2|...|255)"
    """
    result = ""
    first = True
    code = 33
    while code < 256:
        if first:
            result += str(code)
            first = False
        else:
            result += "|" + str(code)
        code += 1
    return "(" + result + ")"
