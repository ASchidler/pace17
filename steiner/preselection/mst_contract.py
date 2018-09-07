from structures import union_find as uf


class MstContract:
    """Based on the idea that any edge between two terminals that is in a minimum spanning tree can be contracted.
    Found in the source code of Krzysztof Maziarz and Adam Polak"""

    def __init__(self, enabled=True):
        self.deleted = []
        self.merged = []
        self._done = False
        self.enabled = enabled

    def reduce(self, steiner, prev_cnt, curr_cnt):
        if len(steiner.terminals) <= 2 or not self.enabled:
            return 0

        steiner.requires_dist(1)

        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])
        components = uf.UnionFind(steiner.graph.nodes)

        i = 0
        while i < len(sorted_edges):
            j = i + 1
            # Find out the maximum index of an edge with the same cost
            while j < len(sorted_edges) and sorted_edges[j][2] == sorted_edges[i][2]:
                j += 1

            # Check all edges with the same cost
            for k in range(i, j):
                (u, v, d) = sorted_edges[k]
                if u in steiner.terminals and v in steiner.terminals:
                    # Finds the indices for the components

                    if components.find(u) != components.find(v):
                        self.deleted.append((u, v, d))

                        for e in steiner.contract_edge(u, v):
                            steiner._voronoi_areas = None
                            steiner._closest_terminals = None
                            steiner.invalidate_steiner(1)
                            steiner.invalidate_dist(1)
                            steiner.invalidate_approx(1)
                            self.merged.append(e)
                            
                        return 1

            # Union in separate loop, otherwise it may cause false negatives
            for k in range(i, j):
                (u, v, d) = sorted_edges[k]
                components.union(u, v)

            i = j

        return 0

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
