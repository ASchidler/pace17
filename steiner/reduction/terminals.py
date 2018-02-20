import networkx as nx
import sys


class TerminalReduction:
    """Tried to reduce the number of terminals.
    This must be the last reduction as it invalidates some of the intermediate results!"""

    def __init__(self):
        self._removed = []
        self._selected = []
        self._selected_merge = []
        self._done = False

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))
        change = True

        while change:
            change = False
            for t in list(steiner.terminals):
                min_val = sys.maxint
                min_node = None
                min_single = False
                neighbors = list(nx.neighbors(steiner.graph, t))

                for n in neighbors:
                    w = steiner.graph[t][n]['weight']

                    if w < min_val:
                        min_node = n
                        min_val = w
                        min_single = True
                    elif w == min_val:
                        min_single = False

                if min_node in steiner.terminals or len(neighbors) == 1:
                    # Only one neighbor? The edge has to be selected, so we can treat the neighbor as a terminal
                    if len(neighbors) == 1:
                        self._removed.append((t, min_node, w))
                        steiner.remove_node(t)
                        steiner.terminals.add(min_node)
                        change = True
                    # The closest node is a terminal? The edge is viable in any optimal solution -> contract edge
                    elif min_node in steiner.terminals and min_single:
                        self._removed.append((t, min_node, min_val))
                        for e in steiner.contract_edge(min_node, t):
                            self._selected.append(e)

                        change = True

        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        cost = solution[1]
        change = False

        if not self._done:
            for (n1, n2, w) in self._removed:
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w
                change = True
            self._done = True

        for (e1, e2) in self._selected:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
