import cut_reachability as cr
import sys


class CutReachabilityEdgeReduction(cr.CutReachabilityReduction):

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

        return cnt

    def post_process(self, solution):
        return solution


