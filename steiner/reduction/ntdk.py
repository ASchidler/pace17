import networkx as nx


# Checks for each node, if the node can be merged
class NtdkReduction:

    def reduce(self, steiner):
        ntdk_edge = 0
        for n in nx.nodes(steiner.graph):
            neighbors = list(nx.all_neighbors(steiner.graph, n))
            degree = len(neighbors)
            true_for_all = True

            if 2 < degree <= 4:
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
                    ntdk_edge = ntdk_edge + 1

        print "NTDK edges " + str(ntdk_edge)
