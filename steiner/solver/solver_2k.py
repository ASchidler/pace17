import networkx as nx
import sys
import heapq

class Solver2k:
    def __init__(self, steiner, terminals, heuristics):
        self.steiner = steiner
        self.terminals = list(terminals)
        self.terminals.sort()
        self.root_node = self.terminals.pop()
        self.max_id = 1 << len(self.terminals)
        self.costs = SolverCosts(self.terminals)
        self.prune_dist = {}
        self.prune_bounds = {}
        self.prune_smt = {}
        self.heuristics = heuristics
        self.labels = {}
        self.result = None
        self.stop = False

    def solve(self):
        # Edge case, may also happen in case of a very efficient preprocessing
        if len(self.steiner.terminals) == 1:
            ret = nx.Graph()
            ret.add_node(list(self.steiner.terminals)[0])
            self.result = ret, 0
            return ret, 0

        """Solves the instance of the steiner tree problem"""
        # Permanent labels => set of completed elements
        p = set()

        for n in nx.nodes(self.steiner.graph):
            self.labels[n] = []

        # Queue entries are tuples (node, terminal set, cost, heuristic value)
        queue = []

        for terminal_set in range(0, len(self.terminals)):
            h = self.heuristic(self.terminals[terminal_set], 1 << terminal_set)
            heapq.heappush(queue, [h, self.terminals[terminal_set], (self.terminals[terminal_set], 1 << terminal_set)])

        # Start algorithm, finish if the root node is added to the tree with all terminals
        while (self.root_node, self.max_id - 1) not in p and not self.stop:
            n = heapq.heappop(queue)[2]

            # Make sure it has not yet been processed (elements may be queued multiple times)
            if (n[0], n[1]) not in p:
                n_key = (n[0], n[1])
                n_cost = self.costs[n_key][0]
                p.add((n[0], n[1]))
                self.labels[n[0]].append(n[1])

                self.process_neighbors(n[0], n_cost, n_key, n[1], p, queue)
                self.process_labels(n[0], n_cost, n_key, n[1], p, queue)

        # Process result
        ret = nx.Graph()
        total = self.backtrack((self.root_node, self.max_id-1), ret)

        self.result = ret, total
        return ret, total

    def process_neighbors(self, n, n_cost, n_key, n_set, p, queue):
        for other_node in nx.neighbors(self.steiner.graph, n):
            other_node_key = (other_node, n_set)
            other_node_cost = self.costs[other_node_key][0]

            total = n_cost + self.steiner.graph[n][other_node]['weight']

            if total < other_node_cost and other_node_key not in p:
                self.costs[other_node_key] = (total, [n_key])
                h = self.heuristic(other_node, n_set)
                if not self.prune(other_node, n_set, total, h):
                    heapq.heappush(queue, [total + h, other_node, (other_node, n_set)])

    def process_labels(self, n, n_cost, n_key, n_set, p, queue):
        for other_set in self.labels[n]:
            # Disjoint?
            if (other_set & n_set) == 0:
                # Set union
                combined = n_set | other_set
                combined_key = (n, combined)

                # Check of not already permanent
                if combined_key not in p:
                    other_set_key = (n, other_set)
                    combined_cost = n_cost + self.costs[other_set_key][0]

                    if combined_cost < self.costs[combined_key][0]:
                        self.costs[combined_key] = (combined_cost, [other_set_key, n_key])
                        h = self.heuristic(n, combined)
                        if not self.prune(n, combined, combined_cost, h, other_set):
                            heapq.heappush(queue, [combined_cost + h, n, (n, combined)])

    def heuristic(self, n, set_id):
        if len(self.heuristics) == 0:
            return 0

        set_id = (self.max_id - 1) ^ set_id
        ts = self.to_list(set_id)
        ts.append(self.root_node)

        max_val = 0
        for h in self.heuristics:
            max_val = max(max_val, h.calculate(n, set_id, ts))

        return max_val

    def prune(self, n, set_id, c, h, set_id2=None):
        # Simple prune
        if c + h > self.steiner.get_approximation().cost:
            return True

        # Complex prune
        target_set = set_id

        if set_id2 is not None:
            target_set = set_id | set_id2

        # First check if there is a bound available
        if target_set not in self.prune_bounds:
            if set_id2 is not None:
                bound = self.prune2_combine(set_id, set_id2)
            else:
                bound = (sys.maxint, [])
        else:
            bound = self.prune_bounds[target_set]

        # Check if pruning is applicable
        if c > bound[0]:
            return True

        # Otherwise check if we have a new upper bound
        dist = self.prune2_dist(target_set)

        # Find the minimum distance between n and R \ set
        ts = self.to_list((self.max_id-1) ^ target_set)
        ts.append(self.root_node)
        for t in ts:
            lt = self.steiner.get_lengths(n, t)
            if lt < dist[0]:
                dist = (lt, t)

        # Check if we can lower the bound
        w = c + dist[0]
        if w < bound[0]:
            self.prune_bounds[target_set] = (w, [dist[1]])

        # In any case do not prune
        return False

    def prune2_dist(self, set_id):
        """Calculates the minimum distance between the cut of terminals in the set and not in the set"""
        if set_id in self.prune_dist:
            return self.prune_dist[set_id], None

        ts1 = []
        ts2 = []

        for i in range(0, len(self.terminals)):
            if ((1 << i) & set_id) > 0:
                ts1.append(self.terminals[i])
            else:
                ts2.append(self.terminals[i])

        ts2.append(self.root_node)

        min_val = sys.maxint
        min_node = None

        for t1 in ts1:
            for t2 in ts2:
                ls = self.steiner.get_lengths(t1, t2)
                if ls < min_val:
                    min_val = ls
                    min_node = t2

        self.prune_dist[set_id] = min_val
        return min_val, min_node

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

    def backtrack(self, c, ret):
        """Creates the solution upon a finished solving run"""

        entry = self.costs[c][1]

        if len(entry) == 0:
            return 0

        # Get the node and the predecessor
        n1 = c[0]

        if len(entry) == 1:
            n2 = entry[0][0]
            w = self.steiner.graph[n1][n2]['weight']
            ret.add_edge(n1, n2, weight=w)
            return w + self.backtrack(entry[0], ret)
        else:
            tmp = 0
            for e in entry:
                tmp = tmp + self.backtrack(e, ret)

            return tmp

    def to_list(self, set_id):
        """Converts a set identifier to the actual set of nodes"""
        ts = []
        for i in range(0, len(self.terminals)):
            if ((1 << i) & set_id) > 0:
                ts.append(self.terminals[i])

        return ts


class SolverCosts(dict):
    """Derived dictionary that uses appropriate default values in case of missing keys"""

    def __init__(self, terminals):
        super(SolverCosts, self).__init__()
        self.terminals = {}
        for i in range(0, len(terminals)):
            self.terminals[terminals[i]] = 1 << i

    def __missing__(self, key):
        # Get node and set ID
        n = key[0]
        s = key[1]

        # Default for empty set is 0
        if s == 0:
            return 0, []
        # Default for a terminal with the set only containing the terminal is 0
        if n in self.terminals and s == self.terminals[n]:
            return 0, []

        # Otherwise infinity
        return sys.maxint, []
