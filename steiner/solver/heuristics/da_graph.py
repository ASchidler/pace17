from heapq import heappush, heappop

class DaGraph:
    def __init__(self, g, r):
        self.g = g
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

            for u, w in self.weights[v].items():
                cst = w + d

                if u not in dist or cst < dist[u]:
                    dist[u] = cst
                    heappush(q, (cst, u))

        return dist

