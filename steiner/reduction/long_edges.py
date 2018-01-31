

# Removes all edges that are longer than the distance to the closest terminal
class LongEdgeReduction:

    def reduce(self, steiner):
        sedges = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            if d > steiner.get_steiner_lengths(u, v):
                sedges = sedges + 1

        print "Steiner edges " + str(sedges)
