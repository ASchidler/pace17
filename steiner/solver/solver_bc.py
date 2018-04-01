import networkx as nx
import scipy.optimize as sp


class SolverBc:
    def __init__(self, steiner, terminals, heuristics):
        self.steiner = steiner
        self.terminals = list(terminals)
        self.heuristics = heuristics
        self.upper_bound = self.steiner.get_approximation().cost
        self.upper_bound_graph = self.steiner.get_approximation().tree
        self.a_ub = []
        self.b_ub = []
        self.a_eq = []
        self.b_eq = []

        self.nodes = list(nx.nodes(self.steiner.graph))

        self.terminals.sort()
        self.nodes.sort()

        self.root = self.terminals.pop()

        # Create cost and edge array. Directional, i.e. each edge is converted to two arcs
        self.costs = []
        self.edges = []

        for (u, v, d) in steiner.graph.edges(data='weight'):
            self.costs.append(d)
            self.costs.append(d)
            self.edges.append((u, v))
            self.edges.append((v, u))

        self.bounds = [(0, 1)] * len(self.edges)

        # Add default rules
        # No incoming edges to root and at least on outgoing for the root node
        root_arr = [0] * len(self.edges)
        for n in nx.neighbors(steiner.graph, self.root):
            # Treat as incoming edge
            idx = self.edges.index((n, self.root))
            self.bounds[idx] = (0, 0)
            # Outgoing edge
            idx = self.edges.index((self.root, n))
            root_arr[idx] = -1

        self.a_ub.append(root_arr)
        self.b_ub.append(-1)

        # Terminals have to have exactly one incoming edge
        for t in self.terminals:
            arr = [0] * len(self.edges)
            for n in nx.neighbors(steiner.graph, t):
                idx = self.edges.index((n, t))
                arr[idx] = 1

            self.a_eq.append(arr)
            self.b_eq.append(1)

        # Non-Terminals have at max one incoming edge
        for n in self.nodes:
            if n not in self.terminals and n != self.root:
                arr = [0] * len(self.edges)
                for n2 in nx.neighbors(steiner.graph, n):
                    # Treat as incoming edge
                    idx = self.edges.index((n2, n))
                    arr[idx] = 1

                self.a_ub.append(arr)
                self.b_ub.append(1)

        # For Non-Terminals, more or equal have to exit than entered (according to paper, this strengthens relaxations)
        for n in self.nodes:
            if n not in self.terminals and n != self.root:
                arr = [0] * len(self.edges)
                for n2 in nx.neighbors(steiner.graph, n):
                    # Treat as incoming edge
                    idx = self.edges.index((n2, n))
                    arr[idx] = 1
                    # Outgoing edge, should be larger
                    idx = self.edges.index((n, n2))
                    arr[idx] = -1

                self.a_ub.append(arr)
                self.b_ub.append(0)

        # For Non-Terminals for any selected outgoing edge, there must be an incoming edge
        for n in self.nodes:
            if n not in self.terminals and n != self.root:
                for na in nx.neighbors(steiner.graph, n):
                    arr = [0] * len(self.edges)
                    idx_out = self.edges.index((n, na))
                    arr[idx_out] = 1
                    for n2 in nx.neighbors(steiner.graph, n):
                        # Treat as incoming edge
                        idx_in = self.edges.index((n2, n))
                        arr[idx_in] = -1

                    self.a_ub.append(arr)
                    self.b_ub.append(0)

        # Not both arcs of an edge can be in a solution (the result is a directed tree)
        for i in range(0, len(self.edges), 2):
            arr = [0] * len(self.edges)
            arr[i] = 1
            arr[i+1] = 1

            self.a_ub.append(arr)
            self.b_ub.append(1)

    def solve(self):
        self.solve_branch(set(), [])
        print "Solution found {}".format(self.upper_bound)
        return self.upper_bound_graph, self.upper_bound

    def solve_branch(self, cuts, fixed):
        c_a_ub = list(self.a_ub)
        c_b_ub = list(self.b_ub)
        c_bounds = list(self.bounds)

        for (idx, val) in fixed:
            c_bounds[idx] = (val, val)

        while True:
            for c_cut in cuts:
                cut_list = [0] * len(self.edges)

                for c_idx in c_cut:
                    cut_list[c_idx] = -1

                c_b_ub.append(-1)
                c_a_ub.append(cut_list)

            # First solve relaxation
            lp = sp.linprog(self.costs, c_a_ub, c_b_ub, self.a_eq, self.b_eq, c_bounds, options={'maxiter': 1000})

            if lp.success and self.check_solved(lp):
                return

            # Check for branching conditions
            if not lp.success or 0 == self.find_cuts(lp, cuts):
                print "Branching"
                return

    def check_solved(self, result):
        epsilon = 0.0000001

        # Check if every var is either 0 or 1
        violated_vars = 0
        for c_x in result.x:
            if (c_x - epsilon) > 0 and (c_x + epsilon) < 1:
                violated_vars += 1

        print "Simplex run, {} violated vars".format(violated_vars)

        if violated_vars == 0:
            result_graph = nx.Graph()
            for i in range(0, len(result.x)):
                if result.x[i] + epsilon >= 1:
                    u, v = self.edges[i][0], self.edges[i][1]
                    result_graph.add_edge(u, v, weight=self.steiner.graph[u][v]['weight'])

            result = result_graph, result_graph.size(weight='weight')

            if result[1] < self.upper_bound:
                self.upper_bound = result[1]
                self.upper_bound_graph = result[0]

            return True

        return False

    def find_cuts(self, result, cuts):
        cuts_prev = len(cuts)
        for t in self.terminals:
            cut_graph = nx.DiGraph()
            for i in range(0, len(result.x)):
                c_edge = self.edges[i]
                cut_graph.add_edge(c_edge[0], c_edge[1], capacity=result.x[i] + 0.000001)

            cut_val, cut_partition = nx.minimum_cut(cut_graph, self.root, t)
            # Violated cut
            while cut_val < 1:
                cut_set = set()
                # Find all incoming edges to the cut
                for n in cut_partition[1]:
                    for n2 in nx.neighbors(self.steiner.graph, n):
                        if n2 not in cut_partition[1]:
                            idx = self.edges.index((n2, n))
                            cut_set.add(idx)
                            cut_graph[n2][n]['capacity'] = 1.000001

                # These steps are necessary to guarantee no duplicate cuts exist
                c_cut = list(cut_set)
                c_cut.sort()
                cuts.add(tuple(c_cut))

                cut_val, cut_partition = nx.minimum_cut(cut_graph, self.root, t)

        print "{} cuts found".format(len(cuts) - cuts_prev)
        return len(cuts) - cuts_prev
