import networkx as nx


class ComponentReduction:
    """ Checks if the graph has several components and removes unnecessary ones"""

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))
        if not nx.is_connected(steiner.graph):
            for c in nx.connected_components(steiner.graph):
                found = False
                for n in c:
                    if n in steiner.terminals:
                        found = True

                if not found:
                    for n in c:
                        steiner.remove_node(n)

        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        return solution, False
