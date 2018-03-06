import networkx as nx
import sys


class LengthTransformReduction:
    """Also called Nearest Special Vertex (NSV) test. """
    def __init__(self):
        self.terminals = None
        self.max_terminal = None
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))
        self.terminals = list(steiner.terminals)
        self.max_terminal = max(self.terminals) + 1

        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])

        # TODO: Calculate once and update...
        mst = nx.minimum_spanning_tree(steiner.graph)
        done = set()

        # Check all edges in the spanning tree
        for (u, v, c1) in mst.edges(data='weight'):
            if u in steiner.terminals:
                tmp = u
                u = v
                v = tmp

            if u not in done and v in steiner.terminals:
                for n in nx.neighbors(mst, u):
                    if n != v and n in steiner.terminals:
                        done.add(u)
                        r1 = self._min_crossing(mst, u, v, sys.maxint, sorted_edges)
                        r2 = self._min_crossing(mst, u, n, sys.maxint, sorted_edges)
                        c2 = mst[u][n]['weight']

                        alpha1 = max(c1, r2 - c2)
                        alpha2 = max(c2, r1 - c1)

                        if alpha1 > alpha2:
                            steiner.graph[u][v]['weight'] = c1 - alpha1
                            steiner.graph[u][n]['weight'] = c2 + alpha2
                        else:
                            steiner.graph[u][v]['weight'] = c1 + alpha1
                            steiner.graph[u][n]['weight'] = c2 - alpha2

        return 0


    def post_process(self, solution):
        change = False
        cost = solution[1]

        if not self._done:
            for (n1, n2, w) in self.deleted:
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w
                change = True
            self._done = True

        for (e1, e2) in self.merged:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]]['weight'] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
