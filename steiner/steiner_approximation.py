import sys
import networkx as nx


class SteinerApproximation:
    """Represents an approximation algorithm for steiner trees for an upper bound. It applies repeated shortest paths"""
    def __init__(self, steiner):
        self.cost = sys.maxint
        self.tree = None

        # TODO: Find a more sophisticated selection strategy?
        limit = min(10, len(steiner.terminals))
        for i in xrange(0, limit):
            result = self.calculate(steiner, len(steiner.terminals) / limit * i)
            if result[1] < self.cost:
                self.cost = result[1]
                self.tree = result[0]
                print "Generated {}".format(self.cost)

        self.vertex_insertion(steiner)
        print "VI {}".format(self.cost)
        #
        # self.cost = 1500660
        # self.tree = nx.Graph()
        #
        # self.tree.add_edge(1, 184)
        # self.tree.add_edge(1, 194)
        # self.tree.add_edge(130, 121)
        # self.tree.add_edge(130, 164)
        # self.tree.add_edge(107, 105)
        # self.tree.add_edge(107, 109)
        # self.tree.add_edge(107, 110)
        # self.tree.add_edge(4, 59)
        # self.tree.add_edge(4, 195)
        # self.tree.add_edge(6, 171)
        # self.tree.add_edge(6, 196)
        # self.tree.add_edge(136, 32)
        # self.tree.add_edge(136, 142)
        # self.tree.add_edge(9, 171)
        # self.tree.add_edge(9, 164)
        # self.tree.add_edge(9, 197)
        # self.tree.add_edge(11, 186)
        # self.tree.add_edge(11, 198)
        # self.tree.add_edge(11, 191)
        # self.tree.add_edge(12, 77)
        # self.tree.add_edge(12, 199)
        # self.tree.add_edge(142, 33)
        # self.tree.add_edge(109, 116)
        # self.tree.add_edge(17, 200)
        # self.tree.add_edge(17, 192)
        # self.tree.add_edge(19, 145)
        # self.tree.add_edge(19, 201)
        # self.tree.add_edge(149, 147)
        # self.tree.add_edge(149, 28)
        # self.tree.add_edge(22, 202)
        # self.tree.add_edge(22, 110)
        # self.tree.add_edge(22, 23)
        # self.tree.add_edge(23, 32)
        # self.tree.add_edge(24, 185)
        # self.tree.add_edge(24, 203)
        # self.tree.add_edge(24, 183)
        # self.tree.add_edge(68, 45)
        # self.tree.add_edge(68, 69)
        # self.tree.add_edge(28, 204)
        # self.tree.add_edge(28, 156)
        # self.tree.add_edge(29, 177)
        # self.tree.add_edge(29, 156)
        # self.tree.add_edge(69, 41)
        # self.tree.add_edge(32, 205)
        # self.tree.add_edge(33, 145)
        # self.tree.add_edge(37, 82)
        # self.tree.add_edge(37, 42)
        # self.tree.add_edge(37, 207)
        # self.tree.add_edge(116, 120)
        # self.tree.add_edge(39, 82)
        # self.tree.add_edge(39, 87)
        # self.tree.add_edge(42, 41)
        # self.tree.add_edge(171, 172)
        # self.tree.add_edge(172, 184)
        # self.tree.add_edge(45, 44)
        # self.tree.add_edge(47, 210)
        # self.tree.add_edge(47, 54)
        # self.tree.add_edge(176, 170)
        # self.tree.add_edge(176, 180)
        # self.tree.add_edge(177, 170)
        # self.tree.add_edge(177, 186)
        # self.tree.add_edge(51, 61)
        # self.tree.add_edge(51, 206)
        # self.tree.add_edge(51, 77)
        # self.tree.add_edge(180, 183)
        # self.tree.add_edge(54, 55)
        # self.tree.add_edge(185, 49)
        # self.tree.add_edge(59, 49)
        # self.tree.add_edge(61, 56)
        # self.tree.add_edge(61, 44)
        # self.tree.add_edge(191, 192)
        # self.tree.add_edge(208, 41)
        # self.tree.add_edge(209, 44)
        # self.tree.add_edge(211, 49)
        # self.tree.add_edge(87, 103)
        # self.tree.add_edge(55, 56)
        # self.tree.add_edge(145, 147)
        # self.tree.add_edge(105, 103)

    def calculate(self, steiner, start):
        # Solution init
        tree = nx.Graph()
        cost = 0

        # Queue -> all terminals must be in solutions and processed nodes
        queue = sorted(list(steiner.terminals))
        nodes = set()

        # Set start node
        nodes.add(queue.pop(start))

        while len(queue) > 0:
            # Find terminal with minimal distance to tree
            min_val = sys.maxint
            min_t = None
            min_n = None

            for t in queue:
                for n in nodes:
                    c = steiner.get_lengths(t, n)

                    if c < min_val:
                        min_val = c
                        min_t = t
                        min_n = n

            # Add to solution
            nodes.add(min_t)
            queue.remove(min_t)

            # Find shortest path between
            path = nx.dijkstra_path(steiner.graph, min_t, min_n)

            # Now backtrack edges
            prev_n = min_t
            for i in range(1, len(path)):
                current_n = path[i]
                if not tree.has_edge(prev_n, current_n):
                    nodes.add(current_n)
                    w = steiner.graph[prev_n][current_n]['weight']
                    cost = cost + w
                    tree.add_edge(prev_n, current_n, weight=w)

                prev_n = current_n

        # Improve solution by creating an MST and deleting non-terminal leafs
        tree = nx.minimum_spanning_tree(tree)

        # Remove non-terminal leafs
        old = sys.maxint
        while old != len(nx.nodes(tree)):
            old = len(nx.nodes(tree))

            for (n, d) in list(nx.degree(tree)):
                if d == 1 and n not in steiner.terminals:
                    tree.remove_node(n)

        # Calculate cost
        cost = 0
        for (u, v, d) in list(tree.edges(data='weight')):
            cost = cost + d

        return tree, cost

    def vertex_insertion(self, steiner):
        for n in nx.nodes(steiner.graph):
            if not self.tree.has_node(n):
                # Find neighbors that are in the solution
                nb = [x for x in nx.neighbors(steiner.graph, n) if self.tree.has_node(x)]

                # With only one intersecting neighbor there is no chance of improvement
                if len(nb) > 1:
                    g = self.tree.copy()

                    # Add first edge
                    g.add_edge(n, nb[0], weight=steiner.graph[n][nb[0]]['weight'])

                    # Try to insert edges and improve result
                    for i in xrange(1, len(nb)):
                        c = steiner.graph[n][nb[i]]['weight']
                        p = list(nx.dijkstra_path(g, n, nb[i]))

                        # Find most expensive edge in path
                        c_max = (None, None, 0)
                        for j in xrange(1, len(p)):
                            c_prime = g[p[j-1]][p[j]]['weight']

                            if c_prime > c_max[2]:
                                c_max = (p[j-1], p[j], c_prime)

                        # If more expensive than the edge we want to insert, try
                        if c_max[2] > c:
                            g.add_edge(n, nb[i], weight=c)
                            g.remove_edge(c_max[0], c_max[1])

                    # Check if the new result is cheaper
                    new_cost = sum((d for (u, v, d) in g.edges(data='weight')))
                    if new_cost < self.cost:
                        self.cost = new_cost
                        self.tree = g


