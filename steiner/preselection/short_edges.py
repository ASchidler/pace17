import networkx as nx
import sys


class ShortEdgeReduction:
    def __init__(self):
        self.terminals = None
        self.max_terminal = None

    def reduce(self, steiner):
        cnt = 0
        self.terminals = list(steiner.terminals)
        self.max_terminal = max(self.terminals) + 1
        mst = nx.minimum_spanning_tree(steiner.graph)
        paths = self._min_paths(steiner)

        # Check all edges in the spanning tree
        for e in mst.edges:
            u = e[0]
            v = e[1]
            r_val = self._min_crossing(steiner, mst, u, v)

            if r_val > 0:
                # Check if edge is part of any shortest path between terminals
                k = self._key(u, v)
                if k in paths:
                    ts = paths[k]

                    for t in ts:
                        d = steiner.get_lengths(t[0], t[1])

                        if r_val >= d:
                            cnt = cnt + 1
                            break

        print "Short edges " + str(cnt)

    # Creates a single key for a combination of nodes, avoid nesting of dictionaries
    def _key(self, n1, n2):
        if n1 > n2:
            return n2 * self.max_terminal + n1
        else:
            return n1 * self.max_terminal + n2

    # Finds the smallest path between terminals
    def _min_paths(self, steiner):
        paths = {}

        # Find shortest paths between terminals
        for i in range(0, len(self.terminals)):
            t1 = self.terminals[i]
            for j in range(i + 1, len(self.terminals)):
                # Find path
                t2 = self.terminals[j]

                l, path = nx.bidirectional_dijkstra(steiner.graph, t1, t2)

                # Convert to edges
                prev = path[0]

                for pi in range(1, len(path)):
                    n = path[pi]
                    k = self._key(prev, n)
                    if k in paths:
                        paths[k].append((t1, t2))
                    else:
                        paths[k] = [(t1, t2)]

                    prev = n

        return paths

    def _min_crossing(self, steiner, mst, n1, n2):
        """Finds the r value of an edge.
            Calculates the cut in the MST and then finds the smallest edge bridging the cut in G"""

        # Calculate the cuts
        mst.remove_edge(n1, n2)
        c = list(nx.connected_components(mst))
        mst.add_edge(n1, n2)

        c1 = set(c[0])
        c2 = set(c[1])

        # Now we have the two cuts, find the smallest edge bridging the cut in the graph
        min_val = sys.maxint
        for (u, v, d) in steiner.graph.edges(data='weight'):
            # Bridges the cut?
            if (u in c1 and v in c2) or (u in c2 and v in c1):
                min_val = min(min_val, d)

        # If the gap is not bridged, the r value is infinite!
        return min_val

    def post_process(self, solution):
        return solution, False
