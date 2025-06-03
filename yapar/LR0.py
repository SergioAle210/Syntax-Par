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
  
    return (lhs, tuple(rhs), dot)


def item_eq(a, b):
    if a[0] != b[0]:
        return False
    arhs = a[1]
    brhs = b[1]
    if len(arhs) != len(brhs):
        return False
    for i in range(len(arhs)):
        if arhs[i] != brhs[i]:
            return False
    if a[2] != b[2]:
        return False
    return True


def item_in(it, items):
    for i in items:
        if item_eq(i, it):
            return True
    return False


def closure(items, grammar):
    closure_set = []
    for i in items:
        closure_set.append(i)
    idx = 0
    while idx < len(closure_set):
        lhs = closure_set[idx][0]
        rhs = closure_set[idx][1]
        dot = closure_set[idx][2]
        if dot < len(rhs):
            B = rhs[dot]
            
            is_nt = False
            for k in grammar.nonterminals:
                if k == B:
                    is_nt = True
                    break
            if is_nt:
                prods = grammar.productions[B]
                for prod in prods:
                    new_item = item(B, prod, 0)
                    if not item_in(new_item, closure_set):
                        closure_set.append(new_item)
        idx += 1
    return closure_set


def goto(I, X, grammar):
    next_items = []
    for it in I:
        lhs = it[0]
        rhs = it[1]
        dot = it[2]
        if dot < len(rhs) and rhs[dot] == X:
            moved = item(lhs, rhs, dot + 1)
            next_items.append(moved)
    if len(next_items) == 0:
        return []
    return closure(next_items, grammar)


def states_eq(a, b):
    if len(a) != len(b):
        return False
    for i in a:
        if not item_in(i, b):
            return False
    for i in b:
        if not item_in(i, a):
            return False
    return True


def state_in(state, states):
    for idx in range(len(states)):
        s = states[idx]
        if states_eq(s, state):
            return idx
    return -1


def lr0_items(grammar):
    initial = item(
        grammar.start_symbol, grammar.productions[grammar.start_symbol][0], 0
    )
    states = []
    transitions = {}

    initial_closure = closure([initial], grammar)
    states.append(initial_closure)
    pending = [initial_closure]
    while len(pending) > 0:
        I = pending[0]
        for rm in range(1, len(pending)):
            pending[rm - 1] = pending[rm]
        pending = pending[:-1]
        src_idx = state_in(I, states)
        symbols = []
        for k in grammar.terminals:
            symbols.append(k)
        for k in grammar.nonterminals:
            symbols.append(k)
        for i in range(len(symbols)):
            X = symbols[i]
            goto_set = goto(I, X, grammar)
            if len(goto_set) > 0:
                idx = state_in(goto_set, states)
                if idx == -1:
                    states.append(goto_set)
                    pending.append(goto_set)
                    idx = len(states) - 1
                transitions[(src_idx, X)] = idx
    return states, transitions, grammar


def visualize_lr0_automaton(
    states, transitions, grammar, filename="output/LRO/lr0_automaton"
):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="TB")
    dot.attr(dpi="600")
    for idx in range(len(states)):
        state = states[idx]
        label = "I" + str(idx) + ":\n"
        for prod in state:
            left = prod[0] + " → "
            before_dot = ""
            for i in range(prod[2]):
                before_dot += prod[1][i] + " "
            left += before_dot
            left += "• "
            after_dot = ""
            for i in range(prod[2], len(prod[1])):
                after_dot += prod[1][i] + " "
            left += after_dot
            label += left.strip() + "\n"
        dot.node(str(idx), label, shape="rectangle")
    for key in transitions:
        src_idx = key[0]
        symbol = key[1]
        dst_idx = transitions[key]
        dot.edge(str(src_idx), str(dst_idx), label=str(symbol))
    dot.render(filename, view=False, cleanup=True)
    with open(filename + ".txt", "w", encoding="utf-8") as f:
        f.write("LR(0) Automaton States:\n")
        for idx in range(len(states)):
            state = states[idx]
            f.write("\nState I" + str(idx) + ":\n")
            for prod in state:
                line = "  " + prod[0] + " → "
                before_dot = ""
                for i in range(prod[2]):
                    before_dot += prod[1][i] + " "
                line += before_dot
                line += "• "
                after_dot = ""
                for i in range(prod[2], len(prod[1])):
                    after_dot += prod[1][i] + " "
                line += after_dot
                f.write(line.strip() + "\n")
        f.write("\nLR(0) Automaton Transitions:\n")
        for key in transitions:
            src_idx = key[0]
            symbol = key[1]
            dst_idx = transitions[key]
            f.write(
                "  I"
                + str(src_idx)
                + " --"
                + str(symbol)
                + "--> I"
                + str(dst_idx)
                + "\n"
            )
