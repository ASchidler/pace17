import networkx as nx
import sys


class TerminalReduction:
    """Tried to reduce the number of terminals.
    This must be the last reduction as it invalidates some of the intermediate results!"""

    def __init__(self):
        self._removed = []
        self._selected = []

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
                    if neighbors == 1:
                        self._removed.append((t, min_node, w))
                        steiner.graph.remove_node(t)
                        steiner.terminals.add(min_node)
                        steiner.terminals.remove(t)
                        change = True
                    elif min_node in steiner.terminals:
                        # TODO: Mechanism for preselection
                        # Since the terminal is already preselection, do not treat as terminal
                        steiner.terminals.remove(t)
                        steiner.graph[t][min_node]['selected'] = True
                        self._selected.append((t, min_node, min_val))
                        change = True

        return track - len(steiner.terminals)

    def post_process(self, solution):
        cost = solution[1]
        change = False
        for (n1, n2, w) in self._removed:
            if not solution[0].has_edge(n1, n2):
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w
                change = True

        # TODO: Idea for preselected edges: Whenever the solver expands a preselected edge, add the neighbor with costs 0
        # TODO: Review if this is indeed correct
        counter = 0
        while counter != len(self._selected):
            for (n1, n2, w) in self._selected:
                # Already in the solution
                if n1 in solution[0].nodes:
                    counter = counter + 1
                # The second conditional is to avoid introducing disconnected components
                elif n1 not in solution[0].nodes and n2 in solution[0].nodes:
                    solution[0].add_edge(n1, n2, weight=w)
                    cost = cost + w
                    change = True
                    counter = counter + 1

        return (solution[0], cost), change
