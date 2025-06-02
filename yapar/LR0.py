import graphviz
import os
import json
import pickle

# --- Representación de la gramática ---
class Grammar:
    def __init__(self, productions, start_symbol):
        self.productions = productions  # dict[str, list[list[str]]]
        self.start_symbol = start_symbol
        self.start_symbol = self._augment_start_symbol(start_symbol, productions)

        # Calcula no terminales y terminales
        self.nonterminals = []
        for nt in productions:
            if nt not in self.nonterminals:
                self.nonterminals.append(nt)
        self.terminals = []
        for nt in productions:
            for body in productions[nt]:
                for sym in body:
                    if sym not in self.nonterminals and sym not in self.terminals:
                        self.terminals.append(sym)
    def _augment_start_symbol(self, base, productions):
        s0 = base + "'"
        while s0 in productions:
            s0 += "'"
        productions[s0] = [[base]]
        return s0



def item(lhs, rhs, dot):
    # Ejemplo: ('E', ['E', '+', 'T'], 2)
    return (lhs, tuple(rhs), dot)

def item_eq(a, b):
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]

def item_in(it, items):
    for i in items:
        if item_eq(i, it):
            return True
    return False


def closure(items, grammar):
    closure_set = [i for i in items]  # copia superficial
    idx = 0
    while idx < len(closure_set):
        lhs, rhs, dot = closure_set[idx]
        if dot < len(rhs):
            B = rhs[dot]
            if B in grammar.nonterminals:
                prods = grammar.productions[B]
                for prod in prods:
                    new_item = item(B, prod, 0)
                    if not item_in(new_item, closure_set):
                        closure_set.append(new_item)
        idx += 1
    # Ordenar para consistencia y evitar duplicados
    return closure_set

def goto(I, X, grammar):
    next_items = []
    for it in I:
        lhs, rhs, dot = it
        if dot < len(rhs) and rhs[dot] == X:
            moved = item(lhs, rhs, dot + 1)
            next_items.append(moved)
    if next_items == []:
        return []
    return closure(next_items, grammar)

def states_eq(a, b):
    if len(a) != len(b):
        return False
    # Cada item en a debe estar en b (sin importar orden)
    for i in a:
        if not item_in(i, b):
            return False
    for i in b:
        if not item_in(i, a):
            return False
    return True

def state_in(state, states):
    for idx, s in enumerate(states):
        if states_eq(s, state):
            return idx
    return -1

def lr0_items(grammar):
    initial = item(grammar.start_symbol, grammar.productions[grammar.start_symbol][0], 0)
    states = []
    transitions = {}  # (origen, simbolo): destino

    initial_closure = closure([initial], grammar)
    states.append(initial_closure)
    pending = [initial_closure]
    while len(pending) > 0:
        I = pending.pop(0)
        src_idx = state_in(I, states)
        for X in grammar.terminals + grammar.nonterminals:
            goto_set = goto(I, X, grammar)
            if goto_set != []:
                idx = state_in(goto_set, states)
                if idx == -1:
                    states.append(goto_set)
                    pending.append(goto_set)
                    idx = len(states) - 1
                transitions[(src_idx, X)] = idx
    return states, transitions, grammar


def visualize_lr0_automaton(states, transitions, grammar, filename="output/LRO/lr0_automaton"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="TB")
    dot.attr(dpi="600")
    for idx, state in enumerate(states):
        label = f"I{idx}:\n"
        label += "\n".join([
            f"{prod[0]} → {' '.join(prod[1][:prod[2]])} • {' '.join(prod[1][prod[2]:])}" for prod in state
        ])
        dot.node(str(idx), label, shape="rectangle")
    for (src_idx, symbol), dst_idx in transitions.items():
        dot.edge(str(src_idx), str(dst_idx), label=symbol)
    dot.render(filename, view=False, cleanup=True)
    # Write states and transitions to a text file
    with open(f"{filename}.txt", "w", encoding="utf-8") as f:
        f.write("LR(0) Automaton States:\n")
        for idx, state in enumerate(states):
            f.write(f"\nState I{idx}:\n")
            for prod in state:
                f.write(f"  {prod[0]} → {' '.join(prod[1][:prod[2]])} • {' '.join(prod[1][prod[2]:])}\n")
        f.write("\nLR(0) Automaton Transitions:\n")
        for (src_idx, symbol), dst_idx in transitions.items():
            f.write(f"  I{src_idx} --{symbol}--> I{dst_idx}\n")
    # Save states and transitions as JSON
    with open("output/LR0/lr0_states.json", "w", encoding="utf-8") as f:
        json.dump([[list(prod) for prod in state] for state in states], f, ensure_ascii=False, indent=2)
    with open("output/LR0/lr0_transitions.json", "w", encoding="utf-8") as f:
        json.dump({f"{src}_{symbol}": dst for (src, symbol), dst in transitions.items()}, f, ensure_ascii=False, indent=2)
    # Save as pickle
    with open("output/LR0/lr0_states.pickle", "wb") as f:
        pickle.dump(states, f)
    with open("output/LR0/lr0_transitions.pickle", "wb") as f:
        pickle.dump(transitions, f)



