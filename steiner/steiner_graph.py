import networkx as nx
import sys
import steiner_approximation as sa


class SteinerGraph:

    def __init__(self):
        self.graph = nx.Graph()
        self.terminals = set()
        self._closest_terminals = None
        self._lengths = {}
        self._steiner_lengths = None
        self._approximation = None
        self._voronoi_areas = None
        self._radius = None
        self._restricted_lengths = {}
        self._restricted_closest = None

    def add_edge(self, n1, n2, c):
        """Adds an edge to the graph. Distances are updated in case it replaces the same edge with higher costs."""
        if self.graph.has_edge(n1, n2):
            orig = self.graph[n1][n2]['weight']
            # Exists, but existing is more expensive
            if orig > c:
                self.graph[n1][n2]['weight'] = c
                self.refresh_distance_matrix(n1, n2, c)
                return True
            # Cheaper edge exists
            else:
                return False

        # Non-existing, simply add. This method
        self.graph.add_edge(n1, n2, weight=c)
        return True

    def remove_edge(self, u, v):
        self.graph.remove_edge(u, v)
        if self.graph.degree[u] == 0:
            self.remove_node(u)
        if self.graph.degree[v] == 0:
            self.remove_node(v)

    def get_lengths(self, n1, n2=None):
        """Retrieve the length of the shortest path between n1 and n2. If n2 is empty all paths from n1 are returned"""
        if n1 not in self._lengths:
            # If non-existing try the other way round. If still not existing calculate
            if n2 is not None and n2 in self._lengths:
                return self._lengths[n2][n1]
            else:
                self._lengths[n1] = nx.single_source_dijkstra_path_length(self.graph, n1)

        # If n2 is empty return the distances to all other nodes
        if n2 is None:
            return self._lengths[n1]

        return self._lengths[n1][n2]

    def get_approximation(self):
        """ Returns an approximation that can be used as an upper bound"""
        if self._approximation is None:
            self._approximation = sa.SteinerApproximation(self)

        return self._approximation

    def calculate_steiner_length(self):
        # Create 2-D dictionary
        self._steiner_lengths = {}
        self.refresh_steiner_lengths()

    def refresh_steiner_lengths(self):
        """ Calculates the steiner distances"""

        g = nx.Graph()

        [g.add_edge(t1, t2, weight=self.get_lengths(t1, t2))
         for t1 in self.terminals for t2 in self.terminals if t2 > t1]

        mst = nx.maximum_spanning_tree(g)

        for (t1, t2) in [(t1, t2) for t1 in self.terminals for t2 in self.terminals if t2 > t1]:
            p = nx.shortest_path(mst, t1, t2)
            max_l = 0
            for i in xrange(1, len(p)):
                max_l = max(max_l, g[p[i-1]][p[i]]['weight'])

            self._steiner_lengths.setdefault(t1, {})[t2] = max_l

    def get_steiner_lengths(self, n1, n2, bound):
        if self._steiner_lengths is None:
            self.calculate_steiner_length()

        if n1 > n2:
            n1, n2 = n2, n1

        # Two terminals? Directly use value
        if n1 in self.terminals and n2 in self.terminals:
            return self._steiner_lengths[n1][n2]

        # The distances to the closest terminal are a lower bound
        cls1 = self.get_closest(n1)
        cls2 = self.get_closest(n2)

        lb = max(self.get_lengths(cls1[0][0], n1), self.get_lengths(cls2[0][0], n2))

        # In case the voronoi region is the same, the lower bound is equal to the upper bound
        # If the lower bound is larger than the bound -> Cannot be satisfied
        if lb > bound or cls1[0][0] == cls2[0][0]:
            return lb

        iterations = range(0, min(len(self.terminals), 3))

        for i, j in ((i, j) for i in iterations for j in iterations):
            t1 = self.get_restricted_closest(n1)[i]
            t2 = self.get_restricted_closest(n2)[j]

            if t1[1] < sys.maxint and t2[1] < sys.maxint:
                if t1[0] > t2[0]:
                    t1, t2 = t2, t1

                val3 = 0 if t1[0] == t2[0] else self._steiner_lengths[t1[0]][t2[0]]
                result = max([t1[1], t2[1], val3])

                if result < bound:
                    return result

        # Since nothing below the bound could be found...
        return sys.maxint

    def path_contains(self, n1, n2, u, v, c):
        path_dist = self.get_lengths(n1, n2)
        dist1 = self.get_lengths(n2, v) + c + self.get_lengths(u, n1)
        dist2 = self.get_lengths(n1, v) + c + self.get_lengths(u, n2)

        dist = min(dist1, dist2)

        if path_dist == dist:
            return True

        return False

    def contract_edge(self, u, v):
        ret = []
        # Contract
        for ng in nx.neighbors(self.graph, v):
            if ng != u:
                d = self.graph[v][ng]['weight']
                if self.add_edge(u, ng, d):
                    ret.append(((u, ng, d), (v, ng, d)))
                else:
                    # There exists an edge to u of equal or cheaper cost
                    alt_c = self.graph[u][ng]['weight']
                    if alt_c < d:
                        self.refresh_distance_matrix(v, ng, alt_c)

        # Refresh distance matrix
        self.refresh_distance_matrix(u, v, 0)

        if v in self.terminals:
            self.move_terminal(v, u)

        self.remove_node(v)

        return ret

    def refresh_distance_matrix(self, u, v, c):
        """ Refreshes the distance matrix under the assumption that u/v has been contracted and has cost c"""
        invalid = []
        # This code really refreshes the distance matrix, but since it may be incomplete, a complete recalc
        # might be necessary
        # for (n1, p) in self._lengths.items():
        #     for (n2, d) in p.items():
        #         # In case of a non-existing node in the distance matrix, leave it to keep the iterator valid
        #         if self.graph.has_node(n2):
        #             # The length of the path under the assumption it is over u, v
        #             dist1 = self.get_lengths(n2, v) + self.get_lengths(u, n1) + c
        #             dist2 = self.get_lengths(n1, v) + self.get_lengths(u, n2) + c
        #             dist = min(dist1, dist2)
        #
        #             if d > dist:
        #                 p[n2] = dist

    def remove_node(self, n):
        if self.graph.has_node(n):
            self.graph.remove_node(n)

        self._lengths.pop(n, None)
        if self._voronoi_areas is not None:
            self._voronoi_areas.pop(n, None)

        if n in self.terminals:
            self.terminals.remove(n)

    def move_terminal(self, tsource, ttarget):
        self.terminals.remove(tsource)

        if self._closest_terminals is not None:
            for i in xrange(0, len(self._closest_terminals)):
                if self._closest_terminals[i] is not None:
                    if self.graph.has_node(i):
                        self._closest_terminals[i] = [x for x in self._closest_terminals[i] if x[0] != tsource]
                        if ttarget not in self.terminals:
                            self._closest_terminals[i].append((ttarget, self.get_lengths(ttarget, i)))
                            self._closest_terminals[i].sort(key=lambda x: x[1])
                    else:
                        self._closest_terminals[i] = None

        if self._restricted_closest is not None:
            for i in xrange(0, len(self._restricted_closest)):
                if self._restricted_closest[i] is not None:
                    if self.graph.has_node(i):
                        self._restricted_closest[i] = [x for x in self._restricted_closest[i] if x[0] != tsource]
                        if ttarget not in self.terminals:
                            self._restricted_closest[i].append((ttarget, self.get_restricted(ttarget, i)))
                            self._restricted_closest[i].sort(key=lambda x: x[1])
                    else:
                        self._restricted_closest[i] = None

        if ttarget not in self.terminals:
            self.terminals.add(ttarget)

            if self._voronoi_areas is not None:
                self._voronoi_areas[ttarget] = set()

        if self._voronoi_areas is not None:
            for n in self._voronoi_areas[tsource]:
                self._voronoi_areas[ttarget].add(n)
            self._voronoi_areas.pop(tsource, None)

            for (k, v) in self._voronoi_areas.items():
                if ttarget in v:
                    v.remove(ttarget)

    def get_voronoi(self):
        if self._voronoi_areas is None:
            self._voronoi_areas = {}
            radius_tmp = {}

            for t in self.terminals:
                self._voronoi_areas[t] = set()
                radius_tmp[t] = sys.maxint

            for n in nx.nodes(self.graph):
                if n not in self.terminals:
                    min_val = sys.maxint
                    min_node = None

                    for t in self.terminals:
                        c = self.get_lengths(t, n)

                        if c < min_val:
                            if min_node is not None:
                                radius_tmp[min_node] = min(radius_tmp[min_node], min_val)
                            min_val = c
                            min_node = t
                        else:
                            radius_tmp[t] = min(radius_tmp[t], c)

                    self._voronoi_areas[min_node].add(n)

            # Try terminal to terminal distances
            for t1, t2 in ((t1, t2) for t1 in self.terminals for t2 in self.terminals if t2 != t1):
                radius_tmp[t1] = min(radius_tmp[t1], self.get_lengths(t1, t2))

            self._radius = [(y, x) for (x, y) in radius_tmp.items()]
            self._radius.sort(key=lambda tup: tup[0])

        return self._voronoi_areas

    def get_closest(self, n):
        if self._closest_terminals is None:
            max_node = max(nx.nodes(self.graph))
            self._closest_terminals = list([None] * (max_node + 1))

        if self._closest_terminals[n] is None:
            self._closest_terminals[n] = [(t, self.get_lengths(t, n)) for t in self.terminals]
            self._closest_terminals[n].sort(key=lambda x: x[1])

        return self._closest_terminals[n]

    def get_radius(self):
        if self._radius is None:
            self.get_voronoi()

        return self._radius

    def get_restricted(self, t, n):
        if t not in self._restricted_lengths:
            g_prime = self.graph.copy()
            for t_prime in self.terminals:
                if t_prime != t:
                    g_prime.remove_node(t_prime)

            self._restricted_lengths[t] = nx.single_source_dijkstra_path_length(g_prime, t)

            # Find shortest paths to other terminals
            for t_prime in self.terminals:
                if t != t_prime:
                    dist = sys.maxint
                    for n in nx.neighbors(self.graph, t_prime):
                        if n == t or n not in self.terminals:
                            dist = min(dist, self._restricted_lengths[t][n] + self.graph[n][t_prime]['weight'])

                    self._restricted_lengths[t][t_prime] = dist

        return self._restricted_lengths[t].setdefault(n, sys.maxint)

    def get_restricted_closest(self, n):
        if self._restricted_closest is None:
            max_node = max(nx.nodes(self.graph))
            self._restricted_closest = list([None] * (max_node + 1))

        if self._restricted_closest[n] is None:
            self._restricted_closest[n] = [(t, self.get_restricted(t, n)) for t in self.terminals]
            self._restricted_closest[n].sort(key=lambda x: x[1])

        return self._restricted_closest[n]
