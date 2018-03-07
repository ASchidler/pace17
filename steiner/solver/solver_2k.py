import networkx as nx
import sys
import heapq


class Solver2k:
    def __init__(self, steiner, terminals, heuristics):
        self.steiner = steiner
        self.max_node = max(nx.nodes(steiner.graph))
        self.terminals = list(terminals)
        self.terminals.sort()
        self.root_node = self.terminals.pop()
        self.max_set = (1 << len(self.terminals)) - 1
        self.prune_dist = {}
        self.prune_bounds = {}
        self.prune_smt = {}
        self.heuristics = heuristics
        self.labels = list([None] * (self.max_node + 1))
        self.result = None
        self.queue = []

        # Pre calculate the IDs of the sets with just the terminal
        self.terminal_ids = {}
        for i in range(0, len(self.terminals)):
            self.terminal_ids[1 << i] = self.terminals[i]

        # Use the approximation + 1 (otherwise solving will fail if the approximation is correct) as an upper cost bound
        self.costs = list([None] * (self.max_node + 1))

        for n in nx.nodes(self.steiner.graph):
            self.labels[n] = []
            s_id = 0
            if n in self.terminals:
                s_id = 1 << (self.terminals.index(n))
            self.costs[n] = SolverCosts(s_id, steiner.get_approximation().cost + 1)

    def solve(self):
        """Solves the instance of the steiner tree problem"""
        # Edge case, may also happen in case of a very efficient preprocessing
        if len(self.steiner.terminals) == 1:
            ret = nx.Graph()
            ret.add_node(list(self.steiner.terminals)[0])
            self.result = ret, 0
            return ret, 0

        # Initialize queue with partial solutions, containing only the terminals themselves
        # Queue format is: (estimated_costs, node, set_id)
        for terminal_id in range(0, len(self.terminals)):
            heapq.heappush(self.queue, [0, self.terminals[terminal_id], 1 << terminal_id])

        # Start algorithm, finish if the root node is added to the tree with all terminals
        while not (self.max_set in self.costs[self.root_node] and self.costs[self.root_node][self.max_set][1]):
            el = heapq.heappop(self.queue)
            n = el[1]
            s = el[2]

            # Make sure it has not yet been processed (elements may be queued multiple times)
            n_cost = self.costs[n][s]
            if not n_cost[1]:
                # Mark permanent
                self.costs[n][s] = (n_cost[0], True, n_cost[2], n_cost[3])
                self.labels[n].append(s)

                self.process_neighbors(n, s, n_cost[0])
                self.process_labels(n, s, n_cost[0])

        # Process result
        ret = nx.Graph()
        total = self.backtrack(self.root_node, self.max_set, ret)

        self.result = ret, total
        return ret, total

    def process_neighbors(self, n, n_set, n_cost):
        for other_node in nx.neighbors(self.steiner.graph, n):
            other_node_cost = self.costs[other_node][n_set]

            # Not permanent
            if not other_node_cost[1]:
                total = n_cost + self.steiner.graph[n][other_node]['weight']
                if total < other_node_cost[0]:
                    # Store costs. The second part of the tuple is backtracking info.
                    self.costs[other_node][n_set] = (total, False, n, False)
                    if not self.prune(other_node, n_set, total):
                        h = self.heuristic(other_node, n_set)
                        if total + h <= self.steiner.get_approximation().cost:
                            heapq.heappush(self.queue, [total + h, other_node, n_set])

    def process_labels(self, n, n_set, n_cost):
        lbl = self.labels[n]
        cst = self.costs[n]
        heuristic = self.heuristic
        prune = self.prune

        # Disjoint?
        for other_set in lbl:
            if (other_set & n_set) == 0:
                # Set union
                combined = n_set | other_set

                # Check of not already permanent
                combined_cost = cst[combined]
                if not combined_cost[1]:
                    total = n_cost + cst[other_set][0]

                    if total < combined_cost[0]:
                        cst[combined] = (total, False, other_set, True)
                        if not prune(n, combined, total, other_set):
                            h = heuristic(n, combined)
                            if total + h <= self.steiner.get_approximation().cost:
                                heapq.heappush(self.queue, [total + h, n, combined])

    def heuristic(self, n, set_id):
        if len(self.heuristics) == 0:
            return 0

        set_id = self.max_set ^ set_id
        ts = self.to_list(set_id)
        ts.append(self.root_node)

        max_val = 0
        for h in self.heuristics:
            max_val = max(max_val, h.calculate(n, set_id, ts))

        return max_val

    def prune(self, n, set_id, c, set_id2=None):
        # Simple prune


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
        ts = self.to_list(self.max_set ^ target_set)
        ts.append(self.root_node)
        for t in ts:
            lt = self.steiner.get_lengths(t, n)
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

        for (s, t) in self.terminal_ids.items():
            if (s & set_id) > 0:
                ts1.append(t)
            else:
                ts2.append(t)

        ts2.append(self.root_node)

        min_val = sys.maxint
        min_node = None

        for (t1, t2) in ((x, y) for x in ts1 for y in ts2):
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

    def backtrack(self, n, s, ret):
        """Creates the solution upon a finished solving run"""

        # To minimize backtracking info stored, the entry contains either the previous node (share the same set)
        # or the previous to sets (share the same node). Or nothing if it is a leaf
        entry = self.costs[n][s]

        if entry[2] is None:
            return 0

        if not entry[3]:
            n2 = entry[2]
            w = self.steiner.graph[n][n2]['weight']
            ret.add_edge(n, n2, weight=w)
            return w + self.backtrack(n2, s, ret)
        else:
            tmp = self.backtrack(n, entry[2], ret)
            tmp = tmp + self.backtrack(n, s ^ entry[2], ret)
            return tmp

    def to_list(self, set_id):
        """Converts a set identifier to the actual set of nodes"""

        return [t for (s, t) in self.terminal_ids.items() if (s & set_id) > 0]


class SolverCosts(dict):
    """Derived dictionary that uses appropriate default values in case of missing keys"""

    def __init__(self, terminal_id, maximum):
        super(SolverCosts, self).__init__()
        self.terminal_id = terminal_id
        self.max_val = maximum

    def __missing__(self, key):
        if key == self.terminal_id:
            return 0, [], None, False

        # Otherwise infinity
        return self.max_val, [], None, False
