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
                # May change during the loop
                if t not in steiner.terminals:
                    continue

                neighbors = list(nx.neighbors(steiner.graph, t))

                if len(neighbors) == 1:
                    self._removed.append((t, neighbors[0], steiner.graph[t][neighbors[0]]['weight']))
                    steiner.move_terminal(t, neighbors[0])
                    steiner.remove_node(t)
                    change = True
                else:
                    contract_edge = None

                    if len(neighbors) == 2:
                        l1, l2 = steiner.graph[t][neighbors[0]]['weight'], steiner.graph[t][neighbors[1]]['weight']
                        if neighbors[0] in steiner.terminals and l1 <= l2:
                            contract_edge = (neighbors[0], l1)
                        elif neighbors[1] in steiner.terminals and l2 <= l1:
                            contract_edge = (neighbors[1], l2)
                    else:
                        min_val = (sys.maxint, None)
                        for n in neighbors:
                            w = steiner.graph[t][n]['weight']

                            # TODO: Is equal really correct? Taken from SCIP Jack code
                            if w < min_val[0] or (w == min_val[0] and n in steiner.terminals):
                                min_val = (w, n)

                        if min_val[1] in steiner.terminals and 1 == len([x for x in neighbors if steiner.graph[t][x]['weight'] == min_val[0]]):
                            contract_edge = (min_val[1], min_val[0])

                    if contract_edge is not None:
                        self._removed.append((t, contract_edge[0], contract_edge[1]))

                        for e in steiner.contract_edge(t, contract_edge[0]):
                            self._selected.append(e)

                        change = True

        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        cost = solution[1]
        change = False

        if not self._done:
            for (n1, n2, w) in self._removed:
                solution[0].add_edge(n1, n2, weight=w)
                cost += w
                change = True
            self._done = True

        for (e1, e2) in self._selected:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]]['weight'] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
