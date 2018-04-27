from heapq import heappush, heappop
from sys import maxint

class TwoPath:

    def reduce(self, steiner, cnt, last_run):
        track = len(steiner.graph.edges)
        nb = steiner.graph._adj
        pop = heappop
        push = heappush
        for t in steiner.terminals:
            for ng, data in nb[t].items():
                if ng in steiner.terminals:
                    continue

                max_w = max(s_data['weight'] for _, s_data in nb[ng].items())
                limit = data['weight'] + max_w
                visited = {ng}
                scanned = {t: 0}
                queue = [(0, t)]
                while queue:
                    c_c, c_n = pop(queue)
                    if c_c > limit:
                        break
                    if c_n in visited:
                        continue

                    visited.add(c_n)

                    for c_b, c_d in nb[c_n].items():
                        dist = c_c + c_d['weight']
                        if c_b not in visited and dist < scanned.setdefault(c_b, maxint):
                            scanned[c_b] = dist
                            push(queue, (dist, c_b))

                #all_contained = all(x in scanned and scanned[x] <= data['weight'] + s_data['weight'] for x, s_data in nb[ng].items())
                all_contained = all(
                    x in scanned and scanned[x] <= s_data['weight'] for x, s_data in nb[ng].items())
                if all_contained:
                    steiner.remove_node(ng)

        steiner.invalidate_steiner(-2)
        steiner.invalidate_dist(-2)
        steiner.invalidate_approx(-2)

        return track - len(steiner.graph.edges)

    def post_process(self, solution):
        return solution, False