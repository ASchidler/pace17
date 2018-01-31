import sys
import networkx as nx


class CutReachabilityReduction:

    def __init__(self):
        self._terminal_minimums = None

    # Find smallest neighbours
    def find_minimums(self, steiner):
        self._terminal_minimums = {}

        for t in steiner.terminals:
            min_val = sys.maxint

            for n in nx.neighbors(steiner.graph, t):
                w = steiner.graph[t][n]['weight']
                min_val = min(w, min_val)

                self._terminal_minimums[t] = min_val

    def reduce(self, steiner):
        cut_cnt = 0
        if self._terminal_minimums is None:
            self.find_minimums(steiner)
            
        approx_nodes = nx.nodes(steiner.get_approximation().tree)
        for n in nx.nodes(steiner.graph):
            if n not in approx_nodes:
                min_val1 = sys.maxint
                min_val2 = sys.maxint
                n1 = None
                n2 = None

                for t in steiner.terminals:
                    d = steiner.get_lengths(t, n)
                    diff = d - self._terminal_minimums[t]

                    if diff <= min_val1:
                        min_val2 = min_val1
                        min_val1 = d
                        n1 = t
                        n2 = n

                min_sum = min_val1 + min_val2

                for t in steiner.terminals:
                    if t != n1 and t != n2:
                        min_sum = min_sum + self._terminal_minimums[t]

                if min_sum >= steiner.get_approximation().cost:
                    cut_cnt = cut_cnt + 1

        print "Cut Reachability " + str(cut_cnt)
