import sys
import networkx as nx
import steiner_graph


class SteinerApproximation:
    def __init__(self, steiner):
        queue = sorted(list(steiner.terminals))
        nodes = set()

        self.cost = 0
        self.tree = nx.Graph()

        nodes.add(queue.pop(0))

        while len(queue) > 0:
            # Find minimal terminal
            min_val = sys.maxint
            min_t = None
            min_n = None

            for t in queue:
                for n in nodes:
                    c = steiner.get_lengths(n, t)

                    if c < min_val:
                        min_val = c
                        min_t = t
                        min_n = n

            nodes.add(min_t)
            queue.remove(min_t)

            path = nx.dijkstra_path(steiner.graph, min_t, min_n)
            prev_n = min_t

            for i in range(1, len(path)):
                current_n = path[i]
                if not self.tree.has_edge(prev_n, current_n):
                    nodes.add(current_n)
                    w = steiner.graph[prev_n][current_n]['weight']
                    self.cost = self.cost + w
                    self.tree.add_edge(prev_n, current_n, weight=w)

                prev_n = current_n

        # Improve solution by creating an MST and deleting non-terminal leafs
        self.tree = nx.minimum_spanning_tree(self.tree)

        old = sys.maxint

        while old != len(nx.nodes(self.tree)):
            old = len(nx.nodes(self.tree))

            for (n, d) in list(nx.degree(self.tree)):
                if d == 1 and n not in steiner.terminals:
                    self.tree.remove_node(n)

        self.cost = 0
        for (u, v, d) in list(self.tree.edges(data='weight')):
            self.cost = self.cost + d
