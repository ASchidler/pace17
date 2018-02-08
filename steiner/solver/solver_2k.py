import networkx as nx
import sortedcontainers as sc
import sys
import math


class Solver2k:
    def __init__(self, steiner):
        self.steiner = steiner
        self.terminals = list(steiner.terminals)
        self.terminals.sort()
        self.root_node = self.terminals.pop()
        self.max_id = 1 << len(self.terminals)
        self.costs = SolverCosts(self.terminals, self.max_id)
        self.msts = {}
        self.tsp = {}
        self.prune_dist = {}
        self.prune_bounds = {}

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
                        if not self.prune(n2, n[1], total, h):
                            queue.add((n2, n[1], total + h, h))

                for i in range(1, self.max_id):
                    if (i & n[1]) == 0 and self.key(n[0], i) in p:
                        combined = n[1] | i
                        c1 = cn + self.costs[self.key(n[0], i)]
                        if c1 < self.costs[self.key(n[0], combined)] and self.key(n[0], combined) not in p:
                            self.costs[self.key(n[0], combined)] = c1
                            b[self.key(n[0], combined)] = [self.key(n[0], i), self.key(n[0], n[1])]
                            h = self.heuristic(n[0], combined)
                            if not self.prune(n2, n[1], c1, h, i):
                                queue.add((n[0], combined, c1 + h, h))

        ret = nx.Graph()
        total = self.backtrack(self.key(self.root_node, self.max_id-1), b, ret)

        return ret, total

    def heuristic(self, n, set_id):
        set_id = (self.max_id - 1) ^ set_id
        ts = self.to_list(set_id)
        ts.append(self.root_node)

        # return 0
        return self.tsp_heuristic(n, set_id, ts)
        # return self.mst_heuristic(n, set_id, ts)

    def mst_heuristic(self, n, set_id, ts):
        # Only one terminal
        if len(ts) == 1:
            return self.steiner.get_lengths(n, ts[0])

        # Calculate MST costs
        cost = self.calc_mst(ts, set_id)

        # Find minimum pairwise distance
        min_val = sys.maxint
        for i in range(0, len(ts)):
            t1 = ts[i]
            l1 = self.steiner.get_lengths(t1, n)
            for j in range(i + 1, len(ts)):
                t2 = ts[j]
                min_val = min(min_val, l1 + self.steiner.get_lengths(t2, n))

        return (min_val + cost) / 2

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

    def tsp_heuristic(self, n, set_id, ts):
        if len(ts) == 1:
            return self.steiner.get_lengths(ts[0], n)

        ts.sort()
        cost = self.get_tsp_for_set(set_id, ts)

        # Find the smallest tour, by adding the node to all possible hamiltonian paths
        min_val = sys.maxint
        for i in range(0, len(ts)):
            t1 = ts[i]
            d1 = self.steiner.get_lengths(t1, n)
            for j in range(i+1, len(ts)):
                t2 = ts[j]
                d2 = self.steiner.get_lengths(t2, n)
                min_val = min(min_val, d1 + d2 + cost[(t1, t2)])

        return int(math.ceil(min_val / 2.0))

    def get_tsp_for_set(self, set_id, ts):
        """ Calculates the Hamiltonian paths for all possible endpoint pairs in the set"""
        if set_id in self.tsp:
            return self.tsp[set_id]

        nodes = list(ts)
        ts = list(nodes)
        self.tsp[set_id] = {}

        for i in range(0, len(ts)):
            t1 = ts[i]
            nodes.remove(t1)

            for j in range(i+1, len(ts)):
                t2 = ts[j]
                # Do not add the endpoint. This would make it a tour, but we need hamiltonian paths
                self.tsp[set_id][(t1, t2)] = self.calc_tsp(t1, nodes, t2) #+ self.steiner.get_lengths(t1, t2)

            nodes.append(t1)
        return self.tsp[set_id]

    def calc_tsp(self, s, nodes, l):
        """ Calculates the shortest path from s to l visiting all nodes """
        if len(nodes) == 1:
            return self.steiner.get_lengths(s, l)

        min_val = sys.maxint
        nodes.remove(l)

        for i in range(0, len(nodes)):
            new_l = nodes[i]
            sub_tsp = self.calc_tsp(s, nodes, new_l)
            min_val = min(min_val, sub_tsp + self.steiner.get_lengths(new_l, l))

        nodes.append(l)
        nodes.sort()

        return min_val

    def prune(self, n, set_id, c, h, set_id2=None):
        if c + h > self.steiner.get_approximation().cost:
            return True

        #return self.prune2(n, set_id, c, h, set_id2)
        return False

    def prune2(self, n, set_id, c, h, set_id2=None):
        if set_id2 is not None:
            set_id = set_id | set_id2
        ts1 = []
        ts2 = []

        for i in range(0, len(self.terminals)):
            if ((1 << i) & set_id) > 0:
                ts1.append(self.terminals[i])
            else:
                ts2.append(self.terminals[i])

        ts2.append(self.root_node)

        min_val = sys.maxint
        if set_id not in self.prune_dist:
            for i in range(0, len(ts1)):
                t1 = ts1[i]

                for j in range(0, len(ts2)):
                    t2 = ts2[j]
                    min_val = min(min_val, self.steiner.get_lengths(t1, t2))

            self.prune_dist[set_id] = min_val
            dist_set = min_val
        else:
            dist_set = self.prune_dist[set_id]

        if set_id not in self.prune_bounds:
            bound = (sys.maxint, [])
        else:
            bound = self.prune_bounds[set_id]

        dist_node = sys.maxint
        for i in range(0, len(ts2)):
            dist_node = min(dist_node, self.steiner.get_lengths(n, ts2[i]))

        w = c + min(dist_set, dist_node)

        if w < bound[0]:
            self.prune_bounds[set_id] = (w, set_id)

        if c > bound[0]:
            return True

        return False

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

    def to_list(self, set_id):
        ts = []
        for i in range(0, len(self.terminals)):
            if ((1 << i) & set_id) > 0:
                ts.append(self.terminals[i])

        return ts


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
