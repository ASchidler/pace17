

class ZeroEdgeReduction:

    def reduce(self, steiner):
        cnt = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            if d == 0:
                cnt = cnt + 1

        print "Zero edges " + str(cnt)
