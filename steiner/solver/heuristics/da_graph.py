from heapq import heappush, heappop


class DaGraph:
    def __init__(self, g, r):
        self.g = g
        # Weights is implicitly the list of predecessors
        self.weights = {}
        self.r = r
        nb = g._adj

        for n in g.nodes:
            self.weights[n] = {n2: w['weight'] for n2, w in nb[n].items()}

    def calc_costs(self):
        fixed = set()
        dist = {}

        q = []

        heappush(q, (0, self.r))

        while q:
            d, v = heappop(q)

            if v in fixed:
                continue
            fixed.add(v)

            for u, _ in self.weights[v].items():
                # weights is the predecessor list...
                cst = self.weights[u][v] + d

                if u not in dist or cst < dist[u]:
                    dist[u] = cst
                    heappush(q, (cst, u))

        return dist

