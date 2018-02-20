import networkx as nx
import sys
import steiner_approximation as sa


class SteinerGraph:

    def __init__(self):
        self.graph = nx.Graph()
        self.terminals = set()
        self._lengths = {}
        self._steiner_lengths = None
        self._approximation = None
        self._voronoi_areas = None

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
        for n in nx.nodes(self.graph):
            self._steiner_lengths[n] = dict(self.get_lengths(n))

        self.refresh_steiner_lengths()

    def refresh_steiner_lengths(self):
        """ Calculates the steiner distances"""

        for n in nx.nodes(self.graph):
            terminals = 0
            visited = set()
            visited.add(n)

            if n in self.terminals:
                terminals = terminals + 1

                while terminals < len(self.terminals):
                    min_val = sys.maxint
                    min_node = None

                    # Closest terminal
                    for t in self.terminals:
                        if t not in visited:
                            c = self._steiner_lengths[n][t]
                            if c < min_val:
                                min_val = c
                                min_node = t

                    terminals = terminals + 1
                    visited.add(min_node)

                    # Calculate steiner distance to nodes
                    for s in nx.nodes(self.graph):
                        if s not in visited:
                            old = self._steiner_lengths[s][n]
                            alt = max(min_val, self._lengths[s][n])

                            if alt <= old:
                                if s not in self.terminals:
                                    visited.add(s)

                                if alt < old:
                                    self._steiner_lengths[n][s] = alt
                                    self._steiner_lengths[s][n] = alt

    def get_steiner_lengths(self, n1, n2):
        if self._steiner_lengths is None:
            self.calculate_steiner_length()

        return self._steiner_lengths[n1][n2]

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
        for (n1, p) in self._lengths.items():
            for (n2, d) in p.items():
                # In case of a non-existing node in the distance matrix, leave it to keep the iterator valid
                if self.graph.has_node(n2):
                    # The length of the path under the assumption it is over u, v
                    dist1 = self.get_lengths(n2, v) + self.get_lengths(u, n1) + c
                    dist2 = self.get_lengths(n1, v) + self.get_lengths(u, n2) + c
                    dist = min(dist1, dist2)

                    if d > dist:
                        p[n2] = dist

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

            for t in self.terminals:
                self._voronoi_areas[t] = set()

            for n in nx.nodes(self.graph):
                if n not in self.terminals:
                    min_val = sys.maxint
                    min_node = None

                    for t in self.terminals:
                        c = self.get_lengths(n, t)
                        if c < min_val:
                            min_val = c
                            min_node = t

                    self._voronoi_areas[min_node].add(n)

        return self._voronoi_areas
