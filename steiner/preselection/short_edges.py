from sys import maxint
from networkx import minimum_spanning_tree, bidirectional_dijkstra
import union_find as uf
from collections import defaultdict


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
        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])
        track = len(sorted_edges)

        non_mst_edges = []
        cps = uf.UnionFind(steiner.graph.nodes)

        nb = defaultdict(list)
        above = defaultdict(list)
        parent = {}
        root = None
        # Shortcut this if all nodes have been found?
        # Build MST
        for (u, v, d) in sorted_edges:
            if cps.find(u) != cps.find(v):
                if root is None:
                    root = u
                cps.union(u, v)
                nb[u].append(v)
                nb[v].append(u)
            else:
                non_mst_edges.append((u, v, d))

        # Establish the order inside the tree
        parent[root] = None
        above[root] = set()
        queue = [root]
        leafs = {root}
        while len(queue) > 0:
            u = queue.pop()
            found = False
            for v in nb[u]:
                if v not in parent:
                    parent[v] = u
                    queue.append(v)
                    leafs.add(v)

                    if u in steiner.terminals:
                        new_above = set(above[u])
                        new_above.add(u)
                        above[v] = new_above
                    else:
                        above[v] = above[u]

                    found = True
            if found:
                leafs.remove(u)

        # Fill with leafs
        queue = defaultdict(list)

        for n in leafs:
            if n in steiner.terminals:
                queue[parent[n]].append((n, {n}, {n}))
            else:
                queue[parent[n]].append((n, {n}, set()))

        # Find bottom up
        while len(queue) > 0:
            new_queue = defaultdict(list)

            for u, entries in queue.items():
                new_subs = set()
                new_terminals = set()
                # Arrived at root
                if parent[u] is None:
                    break

                while len(entries) > 0:
                    v, subs, terminals = entries.pop()
                    new_subs.update(subs)
                    new_terminals.update(terminals)
                    t1 = None
                    t2 = None

                    if len(terminals) == 0:
                        continue

                    for (t, dt) in steiner.get_closest(u):
                        if t in above[u]:
                            t1 = t
                            break

                    if t1 is None:
                        continue

                    for (t, dt) in steiner.get_closest(v):
                        if t in terminals:
                            t2 = t
                            break

                    # Find bridge
                    r_val = maxint
                    for u2, v2, d2 in non_mst_edges:
                        if (u2 in subs and v2 not in subs) or (u2 not in subs and v2 in subs):
                            r_val = d2
                            break

                    if steiner.get_lengths(t1, t2) <= r_val:
                        # Store
                        self.deleted.append((u, v, steiner.graph[u][v]['weight']))

                        for e in steiner.contract_edge(u, v):
                            self.merged.append(e)

                if parent[u] is not None:
                    new_subs.add(u)
                    new_queue[parent[u]].append((u, new_subs, new_terminals))

            queue = new_queue

        result = track - len(steiner.graph.edges)
        if result > 0:
            steiner._voronoi_areas = None
            steiner._closest_terminals = None
            steiner.invalidate_steiner(1)
            steiner.invalidate_dist(1)
            steiner.invalidate_approx(1)

        return result

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
