import networkx as nx
import sortedcontainers as sc
import sys


class Solver2k:
    def __init__(self, steiner):
        self.steiner = steiner
        self.terminals = list(steiner.terminals)
        self.root_node = self.terminals.pop()
        self.max_id = 1 << len(self.terminals)
        self.costs = SolverCosts(self.terminals, self.max_id)
        self.msts = {}

    def key(self, n, s):
        return n * self.max_id + s

    def solve(self):
        p = set()
        b = {}

        for n in nx.nodes(self.steiner.graph):
            p.add(n * self.max_id)

        queue = sc.SortedSet(key=lambda q: q[2])
        for i in range(0, len(self.terminals)):
            queue.add((self.terminals[i], 1 << i, 0, 0))

        while self.key(self.root_node, self.max_id - 1) not in p:
            n = queue.pop(0)
            new_cost = self.costs[self.key(n[0], n[1])] + n[3]

            # Make sure costs didn't change since queuing time
            if new_cost != n[2]:
                queue.add((n[0], n[1], new_cost, n[3]))
            elif self.key(n[0], n[1]) not in p:
                p.add(self.key(n[0], n[1]))

                cn = self.costs[self.key(n[0], n[1])]

                for n2 in nx.neighbors(self.steiner.graph, n[0]):
                    cw = self.costs[self.key(n2, n[1])]
                    total = cn + self.steiner.graph[n[0]][n2]['weight']

                    if total < cw and self.key(n2, n[1]) not in p:
                        self.costs[self.key(n2, n[1])] = total
                        b[self.key(n2, n[1])] = [self.key(n[0], n[1])]
                        h = self.heuristic(n2, n[1])
                        queue.add((n2, n[1], total + h, h))

                for i in range(1, self.max_id):
                    if (i & n[1]) == 0 and self.key(n[0], i) in p:
                        combined = n[1] | i
                        c1 = cn + self.costs[self.key(n[0], i)]
                        if c1 < self.costs[self.key(n[0], combined)] and self.key(n[0], combined) not in p:
                            self.costs[self.key(n[0], combined)] = c1
                            b[self.key(n[0], combined)] = [self.key(n[0], i), self.key(n[0], n[1])]
                            h = self.heuristic(n[0], combined)
                            queue.add((n[0], combined, c1 + h, h))

        ret = nx.Graph()
        total = self.backtrack(self.key(self.root_node, self.max_id-1), b, ret)
        print "Solution found: " + str(total)
        return ret, total

    def heuristic(self, n, set_id):
        return 0

        ts = []

        for i in range(0, len(self.terminals)):
            if ((1 << i) & set_id) > 0:
                ts.append(self.terminals[i])

        # Only one terminal
        if len(ts) == 1:
            return self.steiner.get_lengths(n, ts[0])

        # Calculate MST costs
        cost = self.calc_mst(ts, set_id)

        min_val = sys.maxint

        for i in range(0, len(ts)):
            t1 = ts[i]
            for j in range(i+1, len(ts)):
                t2 = ts[j]
                min_val = min(min_val, (self.steiner.get_lengths(t1, n) + self.steiner.get_lengths(t2, n)) / 2)

        return min_val + cost

    def calc_mst(self, ts, set_id):
        if set_id in self.msts:
            return self.msts[set_id]

        g = nx.Graph()

        for i in range(0, len(ts)):
            t1 = ts[i]
            for j in range(i+1, len(ts)):
                t2 = ts[j]
                g.add_edge(t1, t2, weight=self.steiner.get_lengths(t1, t2))

        cost = 0

        for (u, v, d) in list(nx.minimum_spanning_edges(g)):
            cost = cost + d['weight']

        self.msts[set_id] = cost
        return cost

    def backtrack(self, c, b, ret):
        if c not in b.keys():
            return 0

        n1 = c / self.max_id
        entry = b[c]

        if len(entry) == 1:
            n2 = entry[0] / self.max_id
            w = self.steiner.graph[n1][n2]['weight']
            ret.add_edge(n1, n2, weight=w)
            return w + self.backtrack(entry[0], b, ret)
        else:
            tmp = 0
            for e in entry:
                tmp = tmp + self.backtrack(e, b, ret)

            return tmp


class SolverCosts(dict):
    costs = {}
    terminals = {}
    max_id = None

    def __init__(self, terminals, max_id):
        for i in range(0, len(terminals)):
            self.terminals[terminals[i]] = 1 << i
        self.max_id = max_id

    def __missing__(self, key):
        n = key / self.max_id
        s = key % self.max_id

        if s == 0:
            return 0
        if n in self.terminals and s == self.terminals[n]:
            return 0

        return sys.maxint
