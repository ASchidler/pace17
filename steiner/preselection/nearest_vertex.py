import sys
import networkx as nx


class NearestVertex:
    def __init__(self):
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner):
        cnt = 0

        for t in steiner.terminals:
            if steiner.graph.degree[t] >= 2:
                e1 = (None, sys.maxint)
                e2 = (None, sys.maxint)
                e3 = (None, sys.maxint)

                for n in nx.neighbors(steiner.graph, t):
                    d = steiner.graph[t][n]['weight']

                    if d < e1[1]:
                        e3 = e2
                        e2 = e1
                        e1 = n, d
                    elif d < e2[1]:
                        e3 = e2
                        e2 = n, d
                    elif d < e3[1]:
                        e3 = n, d

                if e1[1] in steiner.get_voronoi()[t]:
                    # Get closest terminal to terminal, since t is closest to t, use second entry
                    cmp_val = steiner.get_closest(t)[1][1]
                else:
                    cmp_val = steiner.get_closest(e1[0])[0][1]

                contract = False
                if e2[1] >= e1[1] + cmp_val:
                    contract = True
                elif steiner.graph.degree[t] == 2 or e3[1] >= e1[1] + cmp_val:
                    true_forall = True
                    for n2 in nx.neighbors(steiner.graph, t):
                        if n2 != e1[0] and n2 != e2[0]:
                            if steiner.graph[t][n2]['weight'] < cmp:
                                true_forall = False
                                break

                    if true_forall:
                        for n2 in nx.neighbors(steiner.graph, e2[0]):
                            if n2 != t:
                                if steiner.graph[e2[0]][n2]['weight'] < cmp:
                                    true_forall = False
                                    break

                    if true_forall:
                        contract = True

                if contract:
                    # Store
                    self.deleted.append((t, e1[0], e1[1]))

                    # Contract
                    for e in steiner.contract_edge(t, e1[0]):
                        self.merged.append(e)

                    cnt += 1

        return cnt

    def post_process(self, solution):
        cost = solution[1]
        change = False

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
