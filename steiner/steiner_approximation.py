import sys
import networkx as nx
import steiner_graph


class SteinerApproximation:
    tree = None
    cost = 0

    def __init__(self, graph):
        queue = list(graph.terminals)
        nodes = set()

        self.cost = 0
        self.tree = nx.Graph()

        nodes.add(queue.pop())

        while len(queue) > 0:
            # Find minimal terminal
            min_val = sys.maxint
            min_t = None
            min_n = None

            for t in queue:
                for n in nodes:
                    c = graph.get_lengths()[n][t]

                    if c < min_val:
                        min_val = c
                        min_t = t
                        min_n = n

            nodes.add(min_t)
            queue.remove(min_t)

            prev_n = None
            for current_n in nx.dijkstra_path(graph.graph, min_t, min_n):
                if prev_n is not None:
                    w = graph.graph[prev_n][current_n]['weight']
                    self.cost = self.cost + w
                    self.tree.add_edge(prev_n, current_n, weight=w)
                prev_n = current_n


        # Improve: MST and then remove non terminal leafs