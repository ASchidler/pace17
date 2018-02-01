import networkx as nx
import sortedcontainers as sc
import sys


class GraphCosts:

    def __init__(self):
        self.costs = None
        self._count = None

    """Calculates the pairwise distance between all nodes"""
    def calculate(self, steiner):
        nodes = sorted(nx.nodes(steiner.graph))
        self._count = len(nodes)
        self.costs = {}

        for i in range(0, len(nodes)):
            n1 = nodes[i]
            for j in range(i+1, len(nodes)):
                n2 = nodes[j]
                self.costs[self._key(n1, n2)] = (sys.maxint, None)

        for n in nodes:
            queue = sc.SortedSet(key=lambda x: x[1])
            queue.add((n, 0))
            processed = set()

            # Copy old results
            for s in nodes:
                if s == n:
                    break

                weight = self.costs[self._key(s, n)][0]
                queue.add((s, weight))

            # Calculate distances
            while len(processed) != len(nodes):
                c = queue.pop(0)

                if c[0] not in processed:
                    processed.add(c[0])
                    for s in nx.neighbors(steiner.graph, c[0]):
                        if s > n:
                            dist = c[1] + steiner.graph[c[0]][s]['weight']

                            idx = self._key(n, s)
                            if dist < self.costs[idx][0]:
                                self.costs[idx] = (dist, c[0])
                                queue.add((s, dist))

    """Calculates a single key based on the two values. Allows the use of a single dictionary"""
    def _key(self, n1, n2):
        if n1 < n2:
            return n1 * self._count + n2
        else:
            return n2 * self._count + n1

    """Returns the length of the path from n1 to n2."""
    def get(self, n1, n2):
        if n1 == n2:
            return 0
        return self.costs[self._key(n1, n2)][0]

    """Returns the path from n1 to n2 as a list of nodes"""
    def path(self, n1, n2):
        if n1 == n2:
            return [n1]

        ret = [n1, n2]
        s = n1
        e = n2
        pivot = 1

        while s != e:
            p = self.costs[self._key(s, e)][1]
            if p != n1 and e != p:
                ret.insert(pivot, p)

            if s < e:
                e = p
            else:
                s = p
                pivot = pivot + 1

        return ret

    def get_row(self, n):
        ret = {}
        for (k, v) in self.costs.items():
            n1 = int(k / self._count)
            n2 = k % self._count
            if n1 == n:
                ret[n2] = v[0]
            elif n2 == n:
                ret[n1] = v[0]

        return ret
