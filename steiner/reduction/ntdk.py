import networkx as nx


class NtdkReduction:
    """ Removes all edges that are longer than the distance to the closest terminal """

    def __init__(self):
        self._removed = {}

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))

        for n in list(nx.nodes(steiner.graph)):
            neighbors = list(nx.all_neighbors(steiner.graph, n))
            degree = len(neighbors)
            true_for_all = True

            if n not in steiner.terminals and 2 < degree <= 4:
                # Powersets
                for power_set in range(1, 1 << degree):
                    # Create complete graph
                    power_graph = nx.Graph()
                    edge_sum = 0
                    for i in range(0, degree):
                        if ((1 << i) & power_set) > 0:
                            n1 = neighbors[i]
                            edge_sum = edge_sum + steiner.graph[n][n1]['weight']

                            for j in range(i + 1, degree):
                                if ((1 << j) & power_set) > 0:
                                    n2 = neighbors[j]
                                    w = steiner.get_steiner_lengths(n1, n2)
                                    power_graph.add_edge(n1, n2, weight=w)

                    mst = list(nx.minimum_spanning_edges(power_graph))

                    mst_sum = 0
                    for edge in mst:
                        mst_sum = mst_sum + power_graph[edge[0]][edge[1]]['weight']

                    true_for_all = true_for_all and mst_sum <= edge_sum

                if true_for_all:
                    nb = list(nx.neighbors(steiner.graph, n))
                    # Introduce artificial edges
                    for i in range(0, len(nb)):
                        n1 = nb[i]
                        c1 = steiner.graph[n][n1]['weight']
                        for j in range(i+1, len(nb)):
                            n2 = nb[j]
                            c2 = steiner.graph[n][n2]['weight']

                            if steiner.add_edge(n1, n2, c1 + c2):
                                self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]

                    steiner.graph.remove_node(n)

        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        change = False
        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                solution[0].add_edge(v[0][0], v[0][1], weight=v[0][2])
                solution[0].add_edge(v[1][0], v[1][1], weight=v[1][2])
                change = True

        return solution, change
