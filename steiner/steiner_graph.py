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

    def add_edge(self, n1, n2, c):
        if self.graph.has_edge(n1, n2):
            if self.graph[n1][n2]['weight'] > c:
                self.graph[n1][n2]['weight'] = c
                return True
            else:
                return False
        self.graph.add_edge(n1, n2, weight=c)
        return True

    def get_lengths(self, n1, n2=None):
        if n1 not in self._lengths:
            if n2 is not None and n2 in self._lengths:
                return self._lengths[n2][n1]
            else:
                self._lengths[n1] = nx.single_source_dijkstra_path_length(self.graph, n1)

        if n2 is None:
            return self._lengths[n1]

        return self._lengths[n1][n2]

    def get_approximation(self):
        if self._approximation is None:
            self._approximation = sa.SteinerApproximation(self)

        return self._approximation

    def calculate_steiner_length(self):
        # Create 2-D dictionary
        self._steiner_lengths = {}

        for n in nx.nodes(self.graph):
            self._steiner_lengths[n] = dict(self.get_lengths(n))

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

        # This is an effect that may occur when using contractions, it happens if a shortest path uses not the
        # contracted edge itself, but if one of the edges shifted from one node to the other occurs on the other node
        if path_dist > dist:
            self._lengths[n1][n2] = dist
            return True

        return False

    def contract_edge(self, u, v, c):
        ret = []
        # Contract
        for ng in nx.neighbors(self.graph, v):
            if ng != u:
                d = self.graph[v][ng]['weight']
                if self.add_edge(u, ng, d):
                    ret.append(((u, ng, d), (v, ng, d)))

        # Refresh distance matrix
        for (n1, p) in self._lengths.items():
            for (n2, d) in p.items():
                # In case of a non-existing node in the distance matrix, leave it to keep the iterator valid
                if self.graph.has_node(n2) and self.path_contains(n1, n2, u, v, c):
                    p[n2] = d - c

        self.remove_node(v)
        self.terminals.add(u)

        return ret

    def remove_node(self, n):
        if self.graph.has_node(n):
            self.graph.remove_node(n)

        self._lengths.pop(n, None)

        if n in self.terminals:
            self.terminals.remove(n)
