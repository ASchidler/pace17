import heapq as hq
from collections import defaultdict
from sys import maxint
import time

class Degree3Distances:
    def __init__(self, steiner, us, ignore):
        self.queue = []
        self.dist = defaultdict(lambda: maxint)
        self.nb = steiner.graph._adj
        self.c_max = 0
        self.ignore = ignore

        for u in us:
            self.queue.append((0, u))
            self.dist[u] = 0

    def get(self, target, limit):
        if target in self.dist:
            return self.dist[target]

        if limit <= self.c_max:
            return limit

        queue = self.queue
        nb = self.nb
        dist = self.dist
        ignore = self.ignore

        while len(queue) > 0:
            d, u = hq.heappop(queue)

            self.c_max = d

            if u == target:
                return d

            if dist[u] != d:
                continue

            for v2, w in nb[u].items():
                d2 = d + w['weight']

                if v2 not in ignore and d2 < dist[v2]:
                    dist[v2] = d2
                    hq.heappush(queue, (d2, v2))

            # Break after expanding the vertex!
            if d >= limit:
                break

        return limit


class Degree3Reduction:
    """Reduction that automatically contracts edges with weight 0. Found in the wata_sigma source code"""

    def __init__(self, enabled=True):
        self.merged = []
        self.enabled = enabled

    def reduce(self, steiner, prev_cnt, curr_cnt):
        track = 0
        nbs = steiner.graph._adj

        if not self.enabled:
            return 0

        start = time.time()

        for u in list(steiner.graph.nodes):
            if u not in steiner.terminals and steiner.graph.degree(u) == 3:
                nb = nbs[u].items()
                total_edge_sum = sum(dta['weight'] for (x, dta) in nb)
                ignore = {u}

                # Calc distances, more memory efficient than calculating it all beforehand
                nbl = nbs[u].keys()
                nbl.sort()
                c_dist = Degree3Distances(steiner, [nbl[0]], ignore)
                dist = {(nbl[0], nbl[1]): c_dist.get(nbl[1], total_edge_sum),
                        (nbl[0], nbl[2]): c_dist.get(nbl[2], total_edge_sum),
                        (nbl[1], nbl[2]): self.sub_dijkstra(steiner, [nbl[1]], nbl[2], ignore, total_edge_sum)
                        }

                #dist = {(x, y): self.sub_dijkstra(steiner, [x], y, ignore, total_edge_sum) for
                #        (x, tt1) in nb for (y, tt2) in nb if y > x}

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
                        c_dist = Degree3Distances(steiner, [x, y], ignore)
                        while 1:
                            # Replace edge by path
                            if c_dist.get(p, up + 1) <= up:
                                delete = True
                                break
                            if p in steiner.terminals:
                                break
                            ignore.add(p)

                            c_dist = Degree3Distances(steiner, [x, y], ignore)
                            ps = []
                            for q, pq in nbs[p].items():
                                pq = pq['weight']
                                if len(ps) < 2 and q not in ignore \
                                        and c_dist.get(q, max(up, pq) + 1) > max(up, pq):
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

        taken = (time.time() - start)
        if len(steiner.graph.edges) > 0 and taken > 0:
            # Percentage of edges removed per second > 0.1%?
            self.enabled = float(track) / float(len(steiner.graph.edges)) / taken > 0.0008

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

            if d > limit:
                break

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
