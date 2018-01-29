import networkx as nx
import sys
import steiner_approximation as sa


class SteinerGraph:
    graph = nx.Graph()
    terminals = set()
    paths = None
    lengths = None
    steiner_lengths = None
    approximation = None

    def parse_graph(self, line):
        lst = line.split(' ')
        if line.startswith("E "):
            self.graph.add_edge(int(lst[1]), int(lst[2]), weight=int(lst[3]))

    def parse_terminal(self, line):
        lst = line.split(' ')
        if line.startswith('T '):
            self.graph.node[int(lst[1])]['terminal'] = True
            self.terminals.add(int(lst[1]))

    def parse_file(self, filename):
        f = open(filename, "r")
        # 0 is start, 1 is graph, 2 are terminals, 3 are decompositions
        parse_mode = 0

        for line in f:
            line = line.strip()
            if line.startswith("END"):
                parse_mode = 0
            elif line.startswith("SECTION Graph"):
                parse_mode = 1
            elif line.startswith("SECTION Terminals"):
                parse_mode = 2
            elif line.startswith("SECTION Tree Decomposition"):
                parse_mode = 3
            elif parse_mode == 1:
                self.parse_graph(line)
            elif parse_mode == 2:
                self.parse_terminal(line)

        # Otherwise ignore

        f.close()

    def get_paths(self):
        if self.paths is None:
            self.paths = dict(nx.all_pairs_dijkstra_path(self.graph))

        return self.paths

    def get_lengths(self):
        if self.lengths is None:
            self.lengths = dict(nx.all_pairs_dijkstra_path_length(self.graph))

        return self.lengths

    def get_approximation(self):
        if self.approximation is None:
            self.approximation = sa.SteinerApproximation(self)

        return self.approximation

    def get_steiner_lengths(self):
        if self.steiner_lengths is not None:
            return self.steiner_lengths

        # Create 2-D dictionary
        self.steiner_lengths = {}

        for n in nx.nodes(self.graph):
            self.steiner_lengths[n] = dict(self.get_lengths()[n])

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
                            c = self.steiner_lengths[n][t]
                            if c < min_val:
                                min_val = c
                                min_node = t

                    terminals = terminals + 1
                    visited.add(min_node)

                    # Calculate steiner distance to nodes
                    for s in nx.nodes(self.graph):
                        if s not in visited:
                            old = self.steiner_lengths[s][n]
                            alt = max(min_val, self.lengths[s][n])

                            if alt <= old:
                                if s not in self.terminals:
                                    visited.add(s)

                                if alt < old:
                                    self.steiner_lengths[n][s] = alt
                                    self.steiner_lengths[s][n] = alt

        return self.steiner_lengths

