import networkx as nx
import sys


class TerminalReduction:
    """Tried to reduce the number of terminals.
    This must be the last reduction as it invalidates some of the intermediate results!"""

    def __init__(self):
        self._removed = []

    def reduce(self, steiner):
        track = len(steiner.terminals)
        change = True
        while change:
            change = False
            for t in list(steiner.terminals):
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
                        self._removed.append((t, min_node, min_val))
                        change = True
                    elif neighbors == 1:
                        self._removed.append((t, min_node, w))
                        steiner.graph.remove_node(t)
                        steiner.terminals.add(min_node)
                        steiner.terminals.remove(t)
                        change = True

        return track - len(steiner.terminals)

    def post_process(self, solution):
        cost = solution[1]
        for (n1, n2, w) in self._removed:
            if not solution[0].has_edge(n1, n2):
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w

        return solution[0], cost
