import networkx as nx


# Removes nodes in disconnected components
class ComponentReduction:

    def reduce(self, steiner):
        if not nx.is_connected(steiner.graph):
            for c in nx.connected_components(steiner.graph):
                found = False
                for n in c:
                    if n in steiner.terminals:
                        found = True

                if not found:
                    print "Found unconnected component of size " + str(len(c))
        else:
            print "Only one component found"
