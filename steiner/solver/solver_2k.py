import heapq
from itertools import chain
from sys import maxint
from networkx import Graph
import set_storage as st


class Solver2k:
    def __init__(self, steiner, terminals, heuristics):
        self.steiner = steiner
        self.max_node = max(steiner.graph.nodes)
        self.terminals = list(terminals)
        self.terminals.sort()
        # Use best root from approximations as base for the algorithm
        target_root = steiner.get_approximation().get_root(self.steiner)
        self.root_node = self.terminals.pop(self.terminals.index(target_root)) \
            if target_root is not None else self.terminals.pop()
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
        steiner.closest_terminals = list([None] * (self.max_node + 1))
        length = steiner.get_lengths

        for n in self.steiner.graph.nodes:
            self.labels[n] = [] #st.SetStorage(len(self.terminals))
            s_id = 0
            if n in self.terminals:
                s_id = 1 << (self.terminals.index(n))
            self.costs[n] = SolverCosts(s_id, steiner.get_approximation().cost + 1)

            # Calc closest terminals per node
            steiner.closest_terminals[n] = [(t, length(t, n)) for t in steiner.terminals]
            steiner.closest_terminals[n].sort(key=lambda x: x[1])

    def solve(self):
        """Solves the instance of the steiner tree problem"""

        # Edge case, may also happen in case of a very efficient preprocessing
        if len(self.steiner.terminals) == 1:
            ret = Graph()
            ret.add_node(list(self.steiner.terminals)[0])
            self.result = ret, 0
            return ret, 0

        # Initialize queue with partial solutions, containing only the terminals themselves
        # Queue format is: (estimated_costs, node, set_id)
        for terminal_id in range(0, len(self.terminals)):
            heapq.heappush(self.queue, (0, (1 << terminal_id) * -1, self.terminals[terminal_id]))

        # Start algorithm, finish if the root node is added to the tree with all terminals
        while not (self.max_set in self.costs[self.root_node] and self.costs[self.root_node][self.max_set][1]):
            old_cost, s, n = heapq.heappop(self.queue)
            s *= -1

            if self.max_set in self.costs[self.root_node]:
                print "Connected to root {}".format(self.costs[self.root_node][self.max_set][0])

            # Make sure it has not yet been processed (elements may be queued multiple times)
            n_cost = self.costs[n][s]
            if not n_cost[1]:
                # Mark permanent
                self.costs[n][s] = (n_cost[0], True, n_cost[2], n_cost[3])
                self.labels[n].append(s)

                self.process_neighbors(n, s, n_cost[0])
                self.process_labels(n, s, n_cost[0])

        # Process result
        ret = Graph()
        total = self.backtrack(self.root_node, self.max_set, ret)

        self.result = ret, total
        return ret, total

    def process_neighbors(self, n, n_set, n_cost):
        nb = self.steiner.graph._adj

        for other_node, dta in nb[n].items():
            other_node_cost = self.costs[other_node][n_set]

            total = n_cost + dta['weight']
            if total < other_node_cost[0]:
                # Store costs. The second part of the tuple is backtracking info.

                h = self.heuristic(other_node, n_set)
                self.costs[other_node][n_set] = (total, False, n, False)
                if total + h <= self.steiner.get_approximation().cost and not self.prune(other_node, n_set, total):
                    heapq.heappush(self.queue, (total + h, n_set * -1, other_node))

    def process_labels(self, n, n_set, n_cost):
        # First localize for better performance
#        lbl = self.labels[n].find_all
        cst = self.costs[n]
        heuristic = self.heuristic
        prune = self.prune
        approx = self.steiner.get_approximation().cost
        q = self.queue
        push = heapq.heappush

#TODO: Fix label store (instance 131 is creating problems)
        for other_set in self.labels[n]:# lbl(n_set):
            if (n_set & other_set) == 0:
                # Set union
                combined = n_set | other_set

                o_cost = cst[other_set][0]
                total = n_cost + o_cost
                combined_cost = cst[combined]

                if total < combined_cost[0]:
                    h = heuristic(n, combined)
                    cst[combined] = (total, False, other_set, True)

                    if total + h <= approx and not prune(n, n_set, total, other_set):
                        push(q, (total + h, combined * -1, n))

    def heuristic(self, n, set_id):
        if len(self.heuristics) == 0:
            return 0

        # Invert set
        set_id = self.max_set ^ set_id
        ts = self.to_list(set_id)
        ts.add(self.root_node)

        max_val = 0
        for h in self.heuristics:
            max_val = max(max_val, h.calculate(n, set_id, ts))

        return max_val

    def prune(self, n, set_id, c, set_id2=0):
        target_set = set_id | set_id2

        try:
            bound = self.prune_bounds[target_set]
        # If no bound is known, try combining one, if the current set is a merge
        except KeyError:
            bound = self.prune2_combine(set_id, set_id2) if set_id2 > 0 else (maxint, [])

        # Check if pruning is applicable
        if c > bound[0]:
            return True

        # Check if there is a new upper bound
        self.prune_check_bound(target_set, n, bound[0], c)

        # In any case do not prune
        return False

    def prune_check_bound(self, set_id, n, bound, c):
        """Calculates the minimum distance between the cut of terminals in the set and not in the set"""

        t_in = []
        t_out = []

        for (s, t) in self.terminal_ids.items():
            if (s & set_id) > 0:
                t_in.append(t)
            else:
                t_out.append(t)

        t_out.append(self.root_node)

        # Find minimum distance between the terminals in the cut and outside the cut
        if set_id in self.prune_dist:
            dist = self.prune_dist[set_id]
        else:
            dist = (maxint, None)
            for t in t_in:
                # Minimum dist from t to cut
                t2, d = next((t2, d) for (t2, d) in self.steiner.get_closest(t) if t2 in t_out)
                if d < dist[0]:
                    dist = (d, t2)

            self.prune_dist[set_id] = dist

        # Find the minimum distance between n and R \ set
        n_t, n_d = next((x, y) for (x, y) in self.steiner.get_closest(n) if x in t_out)
        if n_d < dist[0]:
            dist = (n_d, n_t)

        # Check if we can lower the bound
        w = c + dist[0]
        if w < bound:
            self.prune_bounds[set_id] = (w, [dist[1]])

    def prune2_combine(self, set_id1, set_id2):
        """Calculates a new upper bound using upper bounds from two subsets, if applicable"""

        # Check if bounds for both sets exist
        if not (set_id1 in self.prune_bounds and set_id2 in self.prune_bounds):
            return maxint, []

        set1 = self.to_list(set_id1)
        set2 = self.to_list(set_id2)
        set1_entry = self.prune_bounds[set_id1]
        set2_entry = self.prune_bounds[set_id2]

        # To allow combination of the partial solutions at least one set must be disjoint from the other solutions
        # used nodes
        if any(e in set2 for e in set1_entry[1]) and any(e in set1 for e in set2_entry[1]):
            return maxint, []

        # Combine subset solutions
        val = set1_entry[0] + set2_entry[0]
        s = [x for x in chain(set1_entry[1], set2_entry[1]) if x not in set1 and x not in set2]

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

        return set(t for (s, t) in self.terminal_ids.items() if (s & set_id) > 0)


class SolverCosts(dict):
    """Derived dictionary that uses appropriate default values in case of missing keys"""

    def __init__(self, terminal_id, maximum):
        super(SolverCosts, self).__init__()
        self.terminal_id = terminal_id
        self.max_val = maximum

    def __missing__(self, key):
        if key == self.terminal_id:
            return 0, [], None, False, 0

        # Otherwise infinity
        return self.max_val, [], None, False

