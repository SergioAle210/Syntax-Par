EPS = "λ"  # marca para la producción vacía


def compute_first(g):
    first = {A: set() for A in g}

    changed = True
    while changed:
        changed = False
        for A, prods in g.items():
            for α in prods:
                # α == []  ⇒  ε
                if not α:
                    if EPS not in first[A]:
                        first[A].add(EPS)
                        changed = True
                    continue

                nullable_prefix = True
                for X in α:
                    if X not in g:  # terminal
                        if X not in first[A]:
                            first[A].add(X)
                            changed = True
                        nullable_prefix = False
                        break
                    # X no terminal
                    before = len(first[A])
                    first[A] |= first[X] - {EPS}
                    if len(first[A]) != before:
                        changed = True

                    if EPS in first[X]:  # X ⇒* ε
                        continue
                    nullable_prefix = False
                    break

                if nullable_prefix and EPS not in first[A]:
                    first[A].add(EPS)
                    changed = True
    return first


def compute_follow(g, first, start):
    follow = {A: set() for A in g}
    follow[start].add("$")

    changed = True
    while changed:
        changed = False
        for A, prods in g.items():
            for α in prods:
                trailer = follow[A].copy()  # lo que viene DESPUÉS de la posición
                for X in reversed(α):
                    if X not in g:  # terminal
                        trailer = {X}
                        continue
                    # X no terminal
                    before = len(follow[X])
                    follow[X] |= trailer
                    if len(follow[X]) != before:
                        changed = True

                    if EPS in first[X]:
                        trailer |= first[X] - {EPS}
                    else:
                        trailer = first[X] - {EPS}
    return follow
