from itertools import chain
from sys import maxint
from networkx import Graph
from structures import bounded_structures as bs, d_heap as dh, set_storage as st, steiner_graph as sg
import reduction.dual_ascent as da


class Solver2kConfig:
    """This class contains the parameters for the solver"""
    def __init__(self, heap_width=16, bucket_limit=5000, root_choice=True, use_store=True, use_da=True):
        self.heap_width = heap_width
        self.bucket_limit = bucket_limit
        self.root_choice = root_choice
        self.use_store = use_store
        self.use_da = use_da


class SolverSetLabelStore:
    """This store uses a simple set to manage labels"""

    def __init__(self):
        self._store = set()

    def append(self, label):
        self._store.add(label)

    def find_all(self, label):
        for n in self._store:
            if (n & label) == 0:
                yield n


class SolverInstanceSorter:
    """Sorts the instance so that terminals are first and no gaps are present"""

    def __init__(self):
        self.map_to_original = {}
        self.map_from_original = {}

    def convert(self, steiner, root):
        self.map_to_original[len(steiner.terminals)-1] = root
        self.map_from_original[root] = len(steiner.terminals)-1

        c_term = 0
        c_node = len(steiner.terminals)

        for n in steiner.graph.nodes:
            if n != root:
                if n in steiner.terminals:
                    target = c_term
                    c_term += 1
                else:
                    target = c_node
                    c_node += 1

                self.map_from_original[n] = target
                self.map_to_original[target] = n

        new_steiner = sg.SteinerGraph()
        new_steiner.terminals = set(xrange(0, len(steiner.terminals)))

        nb = steiner.graph._adj

        for u, dta in nb.items():
            u_n = self.map_from_original[u]
            for v, d in dta.items():
                v_n = self.map_from_original[v]
                new_steiner.add_edge(u_n, v_n, d['weight'])

        return new_steiner, len(steiner.terminals) - 1

    def convert_back(self, g):
        new_g = Graph()
        nb = g._adj

        for u, dta in nb.items():
            u_n = self.map_to_original[u]
            for v, d in dta.items():
                v_n = self.map_to_original[v]
                new_g.add_edge(u_n, v_n, weight=d['weight'])

        return new_g


class Solver2k:
    """Solver that uses a mixture of Dijkstra's algorithm and the Dreyfus-Wagner algorithm to solve the SPG.
    As proposed in Hougardy2014"""

    def __init__(self, steiner, terminals, heuristics, config):
        self._last_set_id = None
        self.converter = SolverInstanceSorter()

        # Use best root from approximations as base for the algorithm
        target_root = None
        if config.root_choice:
            target_root = da.DualAscent.root
            if target_root is None or not steiner.graph.has_node(target_root):
                target_root = steiner.get_approximation().get_root(steiner)

        if target_root is None:
            target_root = next(steiner.terminals)

        self.steiner, self.root_node = self.converter.convert(steiner, target_root)
        self.terminals = list(range(0, len(terminals) - 1))

        self.max_node = max(self.steiner.graph.nodes)
        self.the_list_cache = {}

        self.max_set = (1 << len(self.terminals)) - 1
        self.root_set = self.max_set + 1
        self.prune_dist = {}
        self.prune_bounds = {}
        self.heuristic_function = heuristics(self.steiner)
        self.labels = list([None] * (self.max_node + 1))

        if self.steiner.get_approximation().cost <= config.bucket_limit:
            self.queue = bs.create_queue(self.steiner.get_approximation().cost)
            self.pop = bs.dequeue
            self.push = bs.enqueue
        else:
            self.queue = dh.create_queue(config.heap_width)
            self.pop = dh.dequeue
            self.push = dh.enqueue

        # Pre calculate the IDs of the sets with just the terminal
        self.terminal_ids = {}
        for i in range(0, len(self.terminals) + 1):
            self.terminal_ids[1 << i] = self.terminals[i]

        # Use the approximation + 1 (otherwise solving will fail if the approximation is correct) as an upper cost bound
        self.costs = list([None] * (self.max_node + 1))
        self.closest_terminals = list([None] * (self.max_node + 1))
        length = self.steiner.get_lengths

        for n in self.steiner.graph.nodes:
            self.labels[n] = st.SetStorage(len(self.terminals)) if config.use_store else SolverSetLabelStore()
            s_id = 0
            if n in self.terminals:
                s_id = 1 << (self.terminals.index(n))
            self.costs[n] = SolverCosts(s_id, self.steiner.get_approximation().cost + 1)

            # Calc closest terminals per node
            self.closest_terminals[n] = [(1 << t, length(t, n)) for t in self.steiner.terminals]
            self.closest_terminals[n].sort(key=lambda x: x[1])

    def solve(self):
        """Solves the instance of the steiner tree problem"""

        # Edge case, may also happen in case of a very efficient preprocessing
        if len(self.steiner.terminals) == 1:
            ret = Graph()
            ret.add_node(list(self.steiner.terminals)[0])
            return ret, 0

        # Initialize queue with partial solutions, containing only the terminals themselves
        # The queue is keyed by node and terminal subset
        for terminal_id in range(0, len(self.terminals)):
            self.push(self.queue, 0, (1 << terminal_id, self.terminals[terminal_id]))

        pop = self.pop
        root_node = self.root_node
        max_set = self.max_set

        # Start algorithm, finish if the root node is added to the tree with all terminals
        while True:
            s, n = pop(self.queue)

            if s == max_set and n == root_node:
                break

            n_cost = self.costs[n][s][0]
            self.labels[n].append(s)
            self.process_neighbors(n, s, n_cost)
            self.process_labels(n, s, n_cost)

        # Process result
        ret = Graph()
        total = self.backtrack(self.root_node, self.max_set, ret)

        return self.converter.convert_back(ret), total

    def process_neighbors(self, n, n_set, n_cost):
        nb = self.steiner.graph._adj

        for other_node, dta in nb[n].items():
            other_node_cost = self.costs[other_node][n_set]

            total = n_cost + dta['weight']
            if total < other_node_cost[0]:
                # Store costs. The second part of the tuple is backtracking info.
                self.costs[other_node][n_set] = (total, n, False)
                h = self.heuristic(other_node, n_set)

                if total + h <= self.steiner.get_approximation().cost and not self.prune(other_node, n_set, total):
                    self.push(self.queue, total + h, (n_set, other_node))

    def process_labels(self, n, n_set, n_cost):
        # First localize for better performance
        lbl = self.labels[n].find_all
        cst = self.costs[n]
        heuristic = self.heuristic
        prune = self.prune
        approx = self.steiner.get_approximation().cost
        q = self.queue
        push = self.push

        # Union result with all existing labels that are disjoint
        for other_set in lbl(n_set):
            # Set union
            combined = n_set | other_set

            o_cost = cst[other_set][0]
            total = n_cost + o_cost
            combined_cost = cst[combined]

            if total < combined_cost[0]:
                # The costs could be set inside the next conditional. This would maybe save some memory, but since
                # this is a bound before executing the heuristic the next time round, the bound is preferable
                h = heuristic(n, combined)
                cst[combined] = (total, other_set, True)
 
                if total + h <= approx and not prune(n, n_set, total, other_set):
                    push(q, total + h, (combined, n))

    def heuristic(self, n, set_id):
        if self.heuristic_function is None:
            return 0

        # Invert set and add root
        set_id = (self.max_set ^ set_id) | self.root_set

        return self.heuristic_function.calculate(n, set_id)

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

        # Find minimum distance between the terminals in the cut and outside the cut
        if set_id in self.prune_dist:
            dist = self.prune_dist[set_id]
        else:
            dist = (maxint, None)
            for cId, t in self.terminal_ids.items():
                if (cId & set_id) > 0:
                    # Minimum dist from t to cut
                    t2, d = next((t2, d) for (t2, d) in self.closest_terminals[t] if (t2 & set_id) == 0)
                    if d < dist[0]:
                        dist = (d, t2)

            self.prune_dist[set_id] = dist

        # Find the minimum distance between n and R \ set
        n_t, n_d = next((x, y) for (x, y) in self.closest_terminals[n] if (x & set_id) == 0)
        if n_d < dist[0]:
            dist = (n_d, n_t)

        # Check if we can lower the bound
        w = c + dist[0]

        if w < bound:
            self.prune_bounds[set_id] = (w, dist[1])

    def prune2_combine(self, set_id1, set_id2):
        """Calculates a new upper bound using upper bounds from two subsets, if applicable"""

        # Check if bounds for both sets exist
        if not (set_id1 in self.prune_bounds and set_id2 in self.prune_bounds):
            return maxint, []

        set1_entry = self.prune_bounds[set_id1]
        set2_entry = self.prune_bounds[set_id2]

        # To allow combination of the partial solutions at least one set must be disjoint from the other solutions
        # used nodes
        if (set_id2 & set1_entry[1] > 0) and (set_id1 & set2_entry[1] > 0):
            return maxint, []

        # Combine subset solutions
        val = set1_entry[0] + set2_entry[0]
        s = (set1_entry[1] | set2_entry[1]) & ~(set_id1 | set_id2)

        self.prune_bounds[set_id1 | set_id2] = (val, s)
        return val, s

    def backtrack(self, n, s, ret):
        """Creates the solution upon a finished solving run"""

        # To minimize backtracking info stored, the entry contains either the previous node (share the same set)
        # or the previous to sets (share the same node). Or nothing if it is a leaf
        entry = self.costs[n][s]

        if entry[1] is None:
            return 0

        if not entry[2]:
            n2 = entry[1]
            w = self.steiner.graph[n][n2]['weight']
            ret.add_edge(n, n2, weight=w)
            return w + self.backtrack(n2, s, ret)
        else:
            tmp = self.backtrack(n, entry[1], ret)
            tmp = tmp + self.backtrack(n, s ^ entry[1], ret)
            return tmp

    def to_set(self, set_id):
        """Converts a set identifier to the actual set of nodes"""

        ret = set()
        c_term = 0
        while set_id > 0:
            if (set_id & 1) == 1:
                ret.add(c_term)
            set_id >>= 1
            c_term += 1

        return ret

    def to_list(self, set_id):
        """Converts a set identifier to the actual set of nodes"""

        ret = []
        c_term = 0
        while set_id > 0:
            if (set_id & 1) == 1:
                ret.append(c_term)
            set_id >>= 1
            c_term += 1

        return ret


class SolverCosts(dict):
    """Derived dictionary that uses appropriate default values in case of missing keys"""

    def __init__(self, terminal_id, maximum):
        super(SolverCosts, self).__init__()
        self.terminal_id = terminal_id
        self.max_val = maximum

    def __missing__(self, key):
        if key == self.terminal_id:
            return 0, None, False, 0

        # Otherwise infinity
        return self.max_val, None, False
