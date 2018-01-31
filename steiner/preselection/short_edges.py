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
        mst = list(nx.minimum_spanning_edges(steiner.graph))
        paths = self._min_paths(steiner)

        # Check all edges in the spanning tree
        for e in mst:
            u = e[0]
            v = e[1]
            rval = self._min_crossing(steiner, mst, u, v)

            if rval > 0:
                for k, p in paths.items():
                    # Check if edge is part of any shortest path between terminals
                    if (u, v) in p or (v, u) in p:
                        ts = self._unkey(k)
                        d = steiner.get_lengths(ts[0], ts[1])

                        if rval >= d:
                            cnt = cnt + 1

        print "Short edges " + str(cnt)

    # Creates a single key for a combination of nodes, avoid nesting of dictionaries
    def _key(self, n1, n2):
        if n1 > n2:
            return n2 * self.max_terminal + n1
        else:
            return n1 * self.max_terminal + n2

    # Unpacks the single key
    def _unkey(self, k):
        return int(k / self.max_terminal), k % self.max_terminal

    # Finds the smallest path between terminals
    def _min_paths(self, steiner):
        paths = {}

        # Find shortest paths between terminals
        for i in range(0, len(self.terminals)):
            t1 = self.terminals[i]
            for j in range(i + 1, len(self.terminals)):
                # Find path
                t2 = self.terminals[j]
                path = nx.dijkstra_path(steiner.graph, t1, t2)

                # Convert to edges
                prev = path[0]
                set_path = set()
                for pi in range(1, len(path)):
                    n = path[pi]
                    set_path.add((prev, n))
                    prev = n

                # store
                paths[self._key(t1, t2)] = set_path

        return paths


    # Find the r value
    # First the MST is cut at edge (n1,n2), then the smallest edge bridging the cut in G is found
    def _min_crossing(self, steiner, mst, n1, n2):
        # Calculate cuts
        c1 = set()
        c2 = set()

        c1.add(n1)
        c2.add(n2)

        target = nx.number_of_nodes(steiner.graph)

        # TODO: More efficient way possible?
        edges = list(mst)

        while len(c1) + len(c2) != target:
            e = edges.pop(0)
            u = e[0]
            v = e[1]
            # not the current edge
            if u != n1 or v != n2:
                # find the right cut
                if u in c1:
                    c1.add(v)
                elif v in c1:
                    c1.add(u)
                elif u in c2:
                    c2.add(v)
                elif v in c2:
                    c2.add(u)
                # None of the endpoints are known yet -> next iteration
                else:
                    edges.append(e)

        # Now we have the two cuts, find the smallest edge bridging the cut in the graph
        min_val = sys.maxint
        for (u, v, d) in steiner.graph.edges(data='weight'):
            # Bridges the cut?
            if (u in c1 and v in c2) or (u in c2 and v in c1):
                min_val = min(min_val, d)

        # Dont know what happens if none bridges the gap?
        if min_val != sys.maxint:
            return min_val

        return -1

