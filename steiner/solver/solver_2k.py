import networkx as nx
import sortedcontainers as sc
import sys
import math


class Solver2k:
    def __init__(self, steiner, terminals, use_heuristic):
        self.steiner = steiner
        self.terminals = list(terminals)
        self.terminals.sort()
        self.root_node = self.terminals.pop()
        self.max_id = 1 << len(self.terminals)
        self.costs = SolverCosts(self.terminals, self.max_id)
        self.prune_dist = {}
        self.prune_bounds = {}
        self.prune_smt = {}
        self.use_heuristic = use_heuristic

    def key(self, n, s):
        return n * self.max_id + s

    def solve(self):
        # Permanent labels => done set
        p = set()
        # Backtrack information
        b = {}

        for n in nx.nodes(self.steiner.graph):
            p.add(n * self.max_id)

        # Queue entries are tuples (node, terminal set, cost, heuristic value)
        queue = sc.SortedSet(key=lambda q: q[2])
        for other_set in range(0, len(self.terminals)):
            h = self.heuristic(self.terminals[other_set], 1 << other_set)
            queue.add((self.terminals[other_set], 1 << other_set, h, h))

        while self.key(self.root_node, self.max_id - 1) not in p:
            n = queue.pop(0)

            # Make sure it has not yet been processed (elements may be queued multiple times)
            if self.key(n[0], n[1]) not in p:
                n_key = self.key(n[0], n[1])
                p.add(n_key)
                n_cost = self.costs[n_key]

                for n2 in nx.neighbors(self.steiner.graph, n[0]):
                    n2_key = self.key(n2, n[1])
                    n2_cost = self.costs[n2_key]

                    total = n_cost + self.steiner.graph[n[0]][n2]['weight']

                    if total < n2_cost and n2_key not in p:
                        self.costs[n2_key] = total
                        b[n2_key] = [n_key]
                        h = self.heuristic(n2, n[1])
                        if not self.prune(n2, n[1], total, h):
                            queue.add((n2, n[1], total + h, h))

                for other_set in range(1, self.max_id):
                    if (other_set & n[1]) == 0:
                        set_key = self.key(n[0], other_set)
                        if set_key in p:
                            combined = n[1] | other_set
                            combined_key = self.key(n[0], combined)
                            combined_cost = n_cost + self.costs[set_key]
                            if combined_cost < self.costs[combined_key] and combined_key not in p:
                                self.costs[combined_key] = combined_cost
                                b[combined_key] = [set_key, n_key]
                                h = self.heuristic(n[0], combined)
                                if not self.prune(n[0], n[1], combined_cost, h, other_set):
                                    queue.add((n[0], combined, combined_cost + h, h))

        ret = nx.Graph()
        total = self.backtrack(self.key(self.root_node, self.max_id-1), b, ret)

        return ret, total

    def heuristic(self, n, set_id):
        if not self.use_heuristic:
            return 0

        set_id = (self.max_id - 1) ^ set_id
        ts = self.to_list(set_id)
        ts.append(self.root_node)

        #return self.simple_heuristic(n, set_id, ts, 2)

        return max(self.tsp_heuristic(n, set_id, ts), self.mst_heuristic(n, set_id, ts))


    def prune(self, n, set_id, c, h, set_id2=None):
        #if c + h > self.steiner.get_approximation().cost:
        #    return True

        return self.prune2(n, set_id, c, h, set_id2)

    def prune2(self, n, set_id, c, h, set_id2=None):

        if set_id2 is not None:
            set_id1 = set_id
            set_id = set_id | set_id2

        # First check if there is a bound available
        if set_id not in self.prune_bounds:
            #if set_id2 is not None:
            #    bound = self.prune2_combine(set_id1, set_id2)
           # else:
                bound = (sys.maxint, [])
        else:
            bound = self.prune_bounds[set_id]

        if c > bound[0]:
            return True

        # Calculate the minimum distance between the cuts set and R \ set
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
            for t1 in ts1:
                for t2 in ts2:
                    min_val = min(min_val, self.steiner.get_lengths(t1, t2))

            self.prune_dist[set_id] = min_val
            dist_set = min_val
        else:
            dist_set = self.prune_dist[set_id]

        # Find the minimum distance between n and R \ set
        dist_node = sys.maxint
        for t2 in ts2:
            dist_node = min(dist_node, self.steiner.get_lengths(n, t2))

        # Check if we can lower the bound
        w = c + min(dist_set, dist_node)

        if w < bound[0]:
            self.prune_bounds[set_id] = (w, [n])

        # In any case do not prune
        return False

    def prune2_combine(self, set_id1, set_id2):
        if not (set_id1 in self.prune_bounds and set_id2 in self.prune_bounds):
            return sys.maxint, []

        set1 = self.to_list(set_id1)
        set2 = self.to_list(set_id2)
        set1_entry = self.prune_bounds[set_id1]
        set2_entry = self.prune_bounds[set_id2]

        usable = True
        for e in set1_entry[1]:
            if e in set2:
                usable = False

        if not usable:
            usable = True

            for e in set2_entry[1]:
                if e in set1:
                    usable = False

        if not usable:
            return sys.maxint, []

        val = set1_entry[0] + set2_entry[0]
        s = list(set1_entry[1])
        s.extend(set2_entry[1])
        for e in set1:
            if e in s:
                s.remove(e)
        for e in set2:
            if e in s:
                s.remove(e)

        self.prune_bounds[set_id1 | set_id2] = (val, s)
        return val, s

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
    """Derived dictionary that uses appropriate default values in case of missing keys"""

    def __init__(self, terminals, max_id):
        self.terminals = {}
        for i in range(0, len(terminals)):
            self.terminals[terminals[i]] = 1 << i
        self.max_id = max_id

    def __missing__(self, key):
        # Get node and set ID
        n = key / self.max_id
        s = key % self.max_id

        # Default for empty set is 0
        if s == 0:
            return 0
        # Default for a terminal with the set only containing the terminal is 0
        if n in self.terminals and s == self.terminals[n]:
            return 0

        # Otherwise infinity
        return sys.maxint
