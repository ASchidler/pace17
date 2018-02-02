import sys
import networkx as nx


class CutReachabilityReduction:

    def __init__(self):
        self._terminal_minimums = None
        self._terminal_sum = 0

    # Find smallest neighbours
    def find_minimums(self, steiner):
        self._terminal_minimums = {}

        for t in steiner.terminals:
            min_val = sys.maxint

            for n in nx.neighbors(steiner.graph, t):
                w = steiner.graph[t][n]['weight']
                min_val = min(w, min_val)

                self._terminal_minimums[t] = min_val
                self._terminal_sum = self._terminal_sum + min_val

    def reduce_edge(self, steiner):
        cnt = 0

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if not steiner.get_approximation().tree.has_edge(u, v):
                min_u = sys.maxint
                min_u_node = None
                min_u_dist = sys.maxint
                min_v = sys.maxint
                min_v_node = None
                min_v_dist = sys.maxint

                for (t, s) in self._terminal_minimums.items():
                    if u != t:
                        d = steiner.get_lengths(t, u)
                        if d-s < min_u:
                            min_u = d-s
                            min_u_dist = d
                            min_u_node = t

                    if v != t:
                        d = steiner.get_lengths(t, v)
                        if d-s < min_v:
                            min_v = d-s
                            min_v_dist = d
                            min_v_node = t

                total = min_v_dist + min_u_dist
                for (t, s) in self._terminal_minimums.items():
                    if t != min_u_node and t != min_v_node:
                        total = total + s

                if total >= steiner.get_approximation().cost:
                    steiner.graph.remove_edge(u, v)
                    cnt = cnt + 1

        print "Cut R-Edge: " + str(cnt)

    def reduce(self, steiner):
        cut_cnt = 0
        if self._terminal_minimums is None:
            self.find_minimums(steiner)

        self.reduce_edge(steiner)
        approx_nodes = nx.nodes(steiner.get_approximation().tree)
        for n in list(nx.nodes(steiner.graph)):
            if n not in approx_nodes:
                min_val1 = sys.maxint
                min_val2 = sys.maxint
                min_dist1 = sys.maxint
                min_dist2 = sys.maxint
                n1 = None
                n2 = None

                for (t, s) in self._terminal_minimums.items():
                    d = steiner.get_lengths(t, n)
                    diff = d - s

                    if diff < min_val2:
                        if diff < min_val1:
                            min_val2 = min_val1
                            mind_dist2 = min_dist1
                            n2 = n1
                            min_val1 = diff
                            n1 = t
                            min_dist1 = d
                        else:
                            min_dist2 = d
                            min_val2 = diff
                            n2 = t

                # TODO: Is this correct
                if min_val2 == sys.maxint:
                    min_val2 = min_val1
                    n2 = n1
                    min_dist2 = min_dist1

                min_sum = min_dist1 + min_dist2

                for t in steiner.terminals:
                    if t != n1 and t != n2:
                        min_sum = min_sum + self._terminal_minimums[t]

                if min_sum >= steiner.get_approximation().cost:
                    steiner.graph.remove_node(n)
                    cut_cnt = cut_cnt + 1

        print "Cut Reachability " + str(cut_cnt)
