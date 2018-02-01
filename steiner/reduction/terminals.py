import networkx as nx
import sys

"""Tried to reduce the number of terminals"""
class TerminalReduction:

    def __init__(self):
        self._removed = []

    def reduce(self, steiner):
        track = len(steiner.terminals)
        old = sys.maxint
        while old > len(steiner.terminals):
            old = len(steiner.terminals)
            for t in steiner.terminals:
                min_val = sys.maxint
                min_node = None
                neighbors = 0

                for n in nx.neighbors(steiner.graph, t):
                    neighbors = neighbors + 1
                    w = steiner.graph[t][n]['weight']
                    if w < min_val:
                        min_node = n
                        min_val = w

                if min_node in steiner.terminals or neighbors == 1:
                    if min_node in steiner.terminals:
                        # TODO: Mechanism for preselection
                        # Since the terminal is already preselection, do not treat as terminal
                        steiner.terminals.remove(t)
                        break
                    elif neighbors == 1:
                        self._removed.append((t, min_node, w))
                        steiner.graph.remove_node(t)
                        steiner.terminals.add(min_node)
                        steiner.terminals.remove(t)
                        break

                    incidence = incidence + 1

        done = track - len(steiner.terminals)
        print "Removed " + str(done) + " terminals"
