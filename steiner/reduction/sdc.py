import networkx as nx
import heapq as hq
from collections import defaultdict
import sys


class SdcReduction:
    def reduce(self, steiner):
        count = 0
        edge_count = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            edge_count += 1
            # Iteration limit
            if edge_count > 1000:
                break
            result = self.modified_dijkstra(steiner, u, v, d)
            delete = False
            if result[0] is not None:
                delete = result[0]
            else:
                result2 = self.modified_dijkstra(steiner, v, u, d)

                if result2[0] is None:
                    v1, v2 = result[1], result2[1]

                    # Max gets the restricted steiner distance
                    intersection = [max(c1, c2) for (x, c1) in v1.items() for (y, c2) in v2.items() if x == y]
                    for c in intersection:
                        if c <= d:
                            delete = True
                            break

            if delete:
                steiner.remove_edge(u, v)
                count += 1

        return count

    def modified_dijkstra(self, steiner, u, v, d):
        queue = [[0, u]]
        visited = set()
        scanned = defaultdict(lambda: sys.maxint)

        while len(queue) > 0:
            c_val = queue.pop(0)
            n = c_val[1]

            if n == v or c_val[0] > d:
                if c_val[0] <= d:
                    return True, None

                return False, None
            elif n in steiner.terminals and n != u:
                return None, scanned
            # Do not search too far
            elif len(visited) > 10:
                return False, None

            if n in visited:
                continue

            visited.add(n)

            for n2 in nx.neighbors(steiner.graph, n):
                # Do not use current edge
                if not ((n == u and n2 == v) or (n == v and n2 == u)):
                    cost = c_val[0] + steiner.graph[n][n2]['weight']
                    if n2 in steiner.terminals:
                        scanned[n2] = min(scanned[n2], cost)
                    hq.heappush(queue, [cost, n2])

        return False, None

    def post_process(self, solution):
        return solution, False
