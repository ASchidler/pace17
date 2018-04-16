from networkx import is_connected, connected_components


class ComponentReduction:
    """ Checks if the graph has several components and removes unnecessary ones"""

    def __init__(self):
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        track = len(steiner.graph.nodes)
        if len(steiner.graph.nodes) > 1 and not is_connected(steiner.graph):
            for c in list(connected_components(steiner.graph)):
                found = False
                for n in c:
                    if n in steiner.terminals:
                        found = True

                if not found:
                    for n in c:
                        steiner.remove_node(n)

        return track - len(steiner.graph.nodes)

    def post_process(self, solution):
        return solution, False
