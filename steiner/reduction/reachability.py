import sys
import networkx as nx

class ReachabilityReduction:


    def reduce(self, steiner):
        reach_cnt = 0

        approx_nodes = nx.nodes(steiner.get_approximation().tree)

        for n in nx.nodes(steiner.graph):
            if n not in approx_nodes:
                min_val1 = sys.maxint
                min_val2 = sys.maxint
                max_val = 0

                for t in steiner.terminals:
                    d = steiner.get_lengths(t, n)
                    if d < min_val2:
                        if d < min_val1:
                            min_val2 = min_val1
                            min_val1 = d
                        else:
                            min_val2 = d

                    max_val = max(max_val, d)
                # TODO: Is this correct?
                if min_val2 == sys.maxint:
                    min_val2 = min_val1
                if min_val1 != sys.maxint and min_val1 + min_val2 + max_val > steiner.get_approximation().cost:
                    reach_cnt = reach_cnt + 1

        print "Reachability " + str(reach_cnt)
