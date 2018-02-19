import networkx as nx
import sys


class ShortEdgeReduction:
    """Also called Nearest Special Vertex (NSV) test. """
    def __init__(self):
        self.terminals = None
        self.max_terminal = None
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))
        self.terminals = list(steiner.terminals)
        self.max_terminal = max(self.terminals) + 1

        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])

        mst = nx.minimum_spanning_tree(steiner.graph)
        paths = self._min_paths(steiner)

        # Check all edges in the spanning tree
        for (u, v, c) in mst.edges(data='weight'):
            k = self._key(u, v)
            if k in paths:
                ts = paths[k]

                for t in ts:
                    if t[0] not in steiner.terminals or t[1] not in steiner.terminals:
                        continue

                    d = steiner.get_lengths(t[0], t[1])

                    if d <= self._min_crossing(mst, u, v, d, sorted_edges):
                        # Merge edges
                        # First decide how to contract
                        if u in steiner.terminals:
                            n1 = u
                            n2 = v
                        else:
                            n1 = v
                            n2 = u

                        self.deleted.append((n1, n2, c))

                        for ng in nx.neighbors(steiner.graph, n2):
                            if ng != n1:
                                d = steiner.graph[n2][ng]['weight']
                                if steiner.add_edge(n1, ng, d):
                                    self.merged.append(((n1, ng, d), (n2, ng, d)))

                        if n2 in steiner.terminals:
                            steiner.terminals.remove(n2)

                        steiner.terminals.add(n1)
                        steiner.graph.remove_node(n2)

                        break

        # TODO: Another method to find out, if an edge is part of the shortest path, is
        # to check if d(t1,u) + c(u,v) + d(v, t2) == d(t1,t2) (or reverse u and v). May catch more edges
        return track - len(nx.nodes(steiner.graph))

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

    def _min_crossing(self, mst, n1, n2, cutoff, sorted_edges):
        """Finds the r value of an edge. I.e. the smallest edge bridging the mst cut by (n1, n2) in G
        Since we need a value > than d, we use a cutoff value to shorten calculation"""
        queue = [n1]
        nodes = set()

        # Calculate the cut
        while len(queue) > 0:
            n = queue.pop()
            nodes.add(n)

            for b in nx.neighbors(mst, n):
                if b != n2 and b not in nodes:
                    queue.append(b)

        # Find minimum edge bridging the cut
        for (u, v, d) in sorted_edges:
            if d >= cutoff:
                return sys.maxint

            if (u in nodes and v not in nodes) or (v in nodes and u not in nodes):
                return d

        return sys.maxint

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
                if solution[0][e1[0]][e1[1]] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
