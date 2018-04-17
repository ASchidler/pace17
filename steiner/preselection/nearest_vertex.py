from sys import maxint


class NearestVertex:
    def __init__(self):
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        cnt = 0

        for t in list(steiner.terminals):
            # t may have been deleted before
            if t in steiner.terminals and steiner.graph.degree[t] >= 2 and len(steiner.terminals) > 2:
                e1 = (None, maxint, maxint)
                e2 = (None, maxint)
                e3 = (None, maxint)

                # Find three smallest incident edges
                for n in steiner.graph.neighbors(t):
                    d = steiner.graph[t][n]['weight']

                    cmp_val = d + steiner.get_closest(n)[1][1] if n in steiner.get_voronoi()[t] else d + steiner.get_closest(n)[0][1]

                    if d < e1[1] or (d == e1[1] and cmp_val < e1[2]):
                        e3, e2, e1 = e2, e1, (n, d, cmp_val)
                    elif d <= e2[1]:
                        e3, e2 = e2, (n, d)
                    elif d <= e3[1]:
                        e3 = n, d

                cmp_val = e1[2]

                contract = False
                if e2[1] >= cmp_val:
                    contract = True
                elif e2[1] < maxint and e3[1] >= e1[2] and e2[0] not in steiner.terminals:
                    contract = True
                    for n2 in steiner.graph.neighbors(e2[0]):
                        if n2 != t and steiner.graph[e2[0]][n2]['weight'] < e1[2]:
                            contract = False
                            break

                if contract:
                    # Store
                    self.deleted.append((t, e1[0], e1[1]))

                    # Contract
                    for e in steiner.contract_edge(t, e1[0]):
                        self.merged.append(e)

                    cnt += 1
                    steiner._voronoi_areas = None
                    steiner._closest_terminals = None

        if cnt > 0:
            steiner.invalidate_steiner(-1)
            steiner.invalidate_dist(-1)

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




