import heapq as hq
from collections import defaultdict
from sys import maxint


class Degree3Reduction:
    """Reduction that automatically contracts edges with weight 0"""

    def __init__(self):
        self.merged = []
        self.enabled = True

    def reduce(self, steiner, cnt, last_run):
        track = 0
        nbs = steiner.graph._adj

        for u in list(steiner.graph.nodes):
            if u not in steiner.terminals and steiner.graph.degree(u) == 3:
                nb = nbs[u].items()
                total_edge_sum = sum(dta['weight'] for (x, dta) in nb)
                ignore = {u}
                # Calc distances, more memory efficient than calculating it all beforehand
                dist = {(x, y): self.sub_dijkstra(steiner, [x], y, ignore, total_edge_sum) for
                        (x, tt1) in nb for (y, tt2) in nb if y > x}

                for i in range(0, 3):
                    p, up = nb[i]
                    x, ux = nb[(i + 1) % 3]
                    y, uy = nb[(i + 2) % 3]
                    up = up['weight']
                    ux = ux['weight']
                    uy = uy['weight']

                    xp = dist[(min(x, p), max(x, p))]
                    yp = dist[(min(y, p), max(y, p))]
                    xy = dist[(min(x, y), max(x, y))]

                    if xp > ux + up or yp > uy + up:
                        continue

                    # We can reach each node cheaper using the MST among the neighbors
                    if xp + yp + xy - max([xp, yp, xy]) <= ux + uy + up:
                        track += 1
                        steiner.remove_edge(u, p)
                        break
                    else:
                        delete = False
                        while 1:
                            # Replace edge by path
                            if self.sub_dijkstra(steiner, [x, y], p, ignore, up + 1) <= up:
                                delete = True
                                break
                            if p in steiner.terminals:
                                break
                            ignore.add(p)

                            ps = []
                            for q, pq in nbs[p].items():
                                pq = pq['weight']
                                if len(ps) < 2 and q not in ignore \
                                        and self.sub_dijkstra(steiner, [x, y], q, ignore, max(up, pq) + 1) > max(up, pq):
                                    ps.append((q, pq))

                            if len(ps) > 1:
                                break
                            elif len(ps) == 1:
                                p = ps[0][0]
                                up += ps[0][1]
                            else:
                                delete = True
                                break

                        if delete:
                            steiner.remove_edge(u, nb[i][0])
                            track += 1
                            break
        return track

    def sub_dijkstra(self, steiner, us, v, ignore, limit):
        queue = []
        dist = defaultdict(lambda: maxint)
        nb = steiner.graph._adj

        for u in us:
            queue.append((0, u))
            dist[u] = 0

        while len(queue) > 0:
            d, u = hq.heappop(queue)

            if u == v:
                return d

            if dist[u] != d:
                continue

            for v2, w in nb[u].items():
                d2 = d + w['weight']

                if d2 < limit and v2 not in ignore and d2 < dist[v2]:
                    dist[v2] = d2
                    hq.heappush(queue, (d2, v2))

        return limit

    def post_process(self, solution):
        change = False
        return solution, change
