from sys import maxint
from networkx import minimum_spanning_tree, bidirectional_dijkstra

# According to Polzin 04 this test is more complicated than SL and NV and the difference negligible
class ShortEdgeReduction:
    """Also called Nearest Special Vertex (NSV) test. """
    def __init__(self):
        self.terminals = None
        self.max_terminal = None
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        steiner.requires_dist(1)

        track = len(steiner.graph.edges)
        self.terminals = list(steiner.terminals)
        self.max_terminal = max(self.terminals) + 1

        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])

        # TODO: Calculate once and update...
        mst = minimum_spanning_tree(steiner.graph)
        paths = self._min_paths(mst)

        # Check all edges in the spanning tree
        for (u, v, c) in mst.edges(data='weight'):
            k = self._key(u, v)
            if steiner.graph.has_edge(u, v) and steiner.graph.has_node(v) and k in paths:
                min_ts = min(paths[k], key=lambda x: x[0])
                t1, t2, d = min_ts[1], min_ts[2], min_ts[0]

                if t1 not in steiner.terminals or t2 not in steiner.terminals:
                    continue

                if d <= self._min_crossing(mst, u, v, d, sorted_edges):
                    # Merge edges
                    # First decide how to contract
                    if v in steiner.terminals:
                        u, v = v, u

                    # Store
                    self.deleted.append((u, v, c))

                    # Contract
                    for e in steiner.contract_edge(u, v):
                        self.merged.append(e)

                    break

        result = track - len(steiner.graph.edges)
        if cnt > 0:
            steiner.invalidate_steiner(1)
            steiner.invalidate_dist(1)
            steiner.invalidate_approx(1)

        return result

    # Creates a single key for a combination of nodes, avoid nesting of dictionaries
    def _key(self, n1, n2):
        if n1 > n2:
            return n2 * self.max_terminal + n1
        else:
            return n1 * self.max_terminal + n2

    # Finds the smallest path between terminals
    def _min_paths(self, mst):
        paths = {}

        # Find shortest paths between terminals
        for t1, t2 in ((x, y) for x in self.terminals for y in self.terminals if y > x):
                l, path = bidirectional_dijkstra(mst, t1, t2)

                # Convert to edges
                prev = path[0]

                for pi in range(1, len(path)):
                    n = path[pi]
                    k = self._key(prev, n)
                    paths.setdefault(k, []).append((l, t1, t2))
                    prev = n

        return paths

    def _min_crossing(self, mst, n1, n2, cutoff, sorted_edges):
        """Finds the r value of an edge. I.e. the smallest edge bridging the mst cut by (n1, n2) in G
        Since we need a value > than d, we use a cutoff value to shorten calculation"""
        queue = [n1]
        nodes = set()

        # Calculate the cut
        while len(queue) > 0:
            n = queue.pop()
            nodes.add(n)

            for b in mst.neighbors(n):
                if b != n2 and b not in nodes:
                    queue.append(b)

        # Find minimum edge bridging the cut
        for (u, v, d) in sorted_edges:
            if d >= cutoff:
                return maxint

            if (u in nodes and v not in nodes) or (v in nodes and u not in nodes):
                return d

        return maxint

    def post_process(self, solution):
        change = False
        cost = solution[1]

        if not self._done:
            for (n1, n2, w) in self.deleted:
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w
                change = True
            self._done = True

        for (e1, e2) in self.merged:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]]['weight'] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
