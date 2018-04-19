from sys import maxint
from heapq import heappush, heappop, merge
from collections import defaultdict, deque
from itertools import chain
from networkx import Graph, ancestors, dijkstra_path, minimum_spanning_edges, dfs_tree, minimum_spanning_tree, is_connected


# TODO: Optimize the whole thing
class VoronoiPartition:
    def __init__(self, source, target):
        self.regions = {}
        self._closest = {}
        self.source = source
        self._tmp_regions = defaultdict(lambda: {})
        self._tmp_closest = {}
        pop = heappop
        push = heappush

        queue = []
        visited = set()
        nb = source._adj
        # TODO: Use scanned instead of visited?
        # Find voronoi regions. Initialize with tree nodes as voronoi centers
        for n in target.nodes:
            self.regions[n] = {}
            # Queue format is: cost, current node, original start, previous node
            push(queue, [0, n, n, n])

        node_count = len(source.nodes)
        while len(visited) != node_count:
            el = pop(queue)

            if el[1] not in visited:
                visited.add(el[1])
                self.regions[el[2]][el[1]] = (el[0], el[3])
                self._closest[el[1]] = el[2]

                for n, dta in nb[el[1]].items():
                    if n not in visited:
                        cost = el[0] + dta['weight']
                        push(queue, [cost, n, el[2], el[1]])

    def reset(self):
        self._tmp_regions = defaultdict(lambda: {})
        self._tmp_closest = {}

    def repair(self, intermediaries):
        self._tmp_regions = defaultdict(lambda: {})
        self._tmp_closest = {}

        if len(intermediaries) == 0:
            return

        repair_nodes = set()
        visited_repair = set()
        queue = []
        nbs = self.source._adj
        pop = heappop
        push = heappush

        # Find all nodes in the deleted regions
        for p in intermediaries:
            repair_nodes = repair_nodes.union(self.regions[p].keys())

        # Initialize dijkstra s.t. the boundary nodes are added with the distance to the adjacent center
        for rep in repair_nodes:
            for nb, dta in nbs[rep].items():
                c_closest = self._closest[nb]
                if c_closest not in intermediaries:
                    cost = self.regions[c_closest][nb][0] + dta['weight']
                    push(queue, [cost, rep, c_closest, nb])

        # Run dijkstra, limit to dangling nodes
        while len(visited_repair) != len(repair_nodes):
            el = pop(queue)
            if el[1] not in visited_repair:
                visited_repair.add(el[1])
                self._tmp_closest[el[1]] = el[2]
                self._tmp_regions.setdefault(el[2], {})[el[1]] = (el[0], el[3])

                for nb, dta in nbs[el[1]].items():
                    if nb not in visited_repair and nb in repair_nodes:
                        cost = el[0] + dta['weight']
                        push(queue, [cost, nb, el[2], el[1]])

    def extract_path(self, n):
        t = self._tmp_closest[n] if n in self._tmp_closest else self._closest[n]
        vor = self._tmp_regions[t] if t in self._tmp_regions else self.regions[t]

        path = []

        while n != t:
            # This is the switch from the "new" assignment back into assigned territory
            if n not in vor:
                vor = self.regions[t]

            prev = vor[n][1]
            path.append((n, prev, self.source[n][prev]['weight']))
            n = prev

        # returns path and endpoint
        return path, n

    def dist(self, n):
        if n in self._tmp_closest:
            return self._tmp_regions[self._tmp_closest[n]][n][0]
        else:
            return self.regions[self._closest[n]][n][0]

    def closest(self, n):
        if n in self._tmp_closest:
            return self._tmp_closest[n]

        return self._closest[n]


class SteinerApproximation:
    good_roots = deque(maxlen=10)

    """Represents an approximation algorithm for steiner trees for an upper bound. It applies repeated shortest paths"""
    def __init__(self, steiner, optimize=True, limit=20):
        self.cost = maxint
        self.tree = None
        self._root = None
        self.steiner = steiner
        self._descendants = None

        steiner.requires_dist(0)

        # Select roots, based on previous good roots
        limit = min(limit, len(steiner.terminals))
        target_roots = set()
        seed = 1
        while SteinerApproximation.good_roots and len(target_roots) <= limit / 2:
            el = SteinerApproximation.good_roots.pop()
            if steiner.graph.has_node(el):
                target_roots.add(el)
                seed = el
        SteinerApproximation.good_roots.clear()

        ts = list(steiner.terminals)

        for idx in ((i * 196613 + seed) % len(ts) for i in range(1, len(ts) + 1)):
            if len(target_roots) == limit:
                break
            el = ts[idx]
            seed = el
            target_roots.add(el)

        results = [(self.calculate2(steiner, start_node), start_node) for start_node in target_roots]
        results.sort(key=lambda x: x[0][1])
        for i in reversed(range(0, len(results))):
            SteinerApproximation.good_roots.append(results[i][1])

        (self.tree, self.cost), self._root = results[0]

        if optimize:
            self.optimize()

    def get_root(self, g):
        # Make sure root is a terminal, otherwise take the closest (may happen if base graph was reduced)
        if self._root not in g.terminals:
            nb = self.tree._adj
            queue = [(0, self._root)]
            visited = set()
            while queue:
                d, n = heappop(queue)

                if n in g.terminals:
                    self._root = n
                    break

                if n in visited:
                    continue

                for n2, dta in nb[n].items():
                    if n2 not in visited:
                        heappush(queue, (d + dta['weight'], n2))

        return self._root

    def optimize(self):
        prev = 0

        while prev != self.cost:
            prev = self.cost
            self.keyvertex_deletion(self.steiner)
            self.path_exchange(self.steiner, False)
            self.vertex_insertion(self.steiner)

            # Remove non-terminal leafs
            old = maxint
            while old != len(self.tree.nodes):
                old = len(self.tree.nodes)

                for (n, d) in list(self.tree.degree()):
                    if d == 1 and n not in self.steiner.terminals:
                        self.tree.remove_node(n)

    @staticmethod
    def calculate(steiner, start_node):
        # Solution init
        tree = Graph()

        # Queue -> all terminals must be in solutions and processed nodes
        queue = [x for x in steiner.terminals if x != start_node]
        tree.add_node(start_node)

        while queue:
            # Find terminal with minimal distance to tree
            t, n = min(((t, n) for t in queue for n in tree.nodes), key=lambda el: steiner.get_lengths(el[0], el[1]))

            # Mark result
            queue.remove(t)

            # Find shortest path between tree and terminal
            path = dijkstra_path(steiner.graph, t, n)

            # Now add the path to the tree
            c_node = path.pop()
            while path:
                c_next = path.pop()
                tree.add_edge(c_node, c_next, weight=steiner.graph[c_node][c_next]['weight'])
                c_node = c_next

        # Improve solution by creating an MST and deleting non-terminal leafs
        tree = minimum_spanning_tree(tree)

        # Remove non-terminal leafs
        old = maxint
        while old != len(tree.nodes):
            old = len(tree.nodes)

            for (n, d) in list(tree.degree()):
                if d == 1 and n not in steiner.terminals:
                    tree.remove_node(n)

        # Calculate cost
        cost = sum(d for (u, v, d) in tree.edges(data='weight'))
        return tree, cost

    @staticmethod
    def calculate2(steiner, start_node):
        tree = Graph()
        tree.add_node(start_node)
        nb = steiner.graph._adj

        scanned = {start_node: (0, 0, 0)}
        p = {start_node: None}
        queue = []
        remaining = {t for t in steiner.terminals if t != start_node}

        def _expand_node(expand_n, base_cost, randomizer):
            """Expands a single node. Sets cost, previous and queue status for neighboring nodes"""

            for next_n, props in nb[expand_n].items():
                randomizer -= 1
                total_cost = props['weight'] + base_cost
                e_cost = (total_cost, props['weight'], randomizer)

                # Check for tree membership as this signifies a loop back to the tree
                if next_n not in scanned or e_cost < scanned[next_n] and not tree.has_node(next_n):
                    heappush(queue, (e_cost[0], e_cost[1], e_cost[2], next_n))
                    scanned[next_n] = e_cost
                    p[next_n] = expand_n

        # Pre-Expand root
        _expand_node(start_node, 0, 0)

        while remaining:
            cost, pw, rd, n = heappop(queue)

            if n in remaining:
                remaining.remove(n)

                # Find path to tree
                c_node = n
                path = []
                while not tree.has_node(c_node):
                    path.append(c_node)
                    tree.add_node(c_node)
                    c_node = p[c_node]

                # c_node now contains node that is in the tree, but not in path
                # add path to tree
                while path:
                    c_next = path.pop()
                    tree.add_edge(c_node, c_next, weight=nb[c_node][c_next]['weight'])
                    _expand_node(c_next, 0, 0)
                    c_node = c_next
            else:
                _expand_node(n, cost, rd)

        # Prune by using an MST and clearing non-terminal leafs
        tree = minimum_spanning_tree(tree)

        # Remove non-terminal leafs
        old = maxint
        while old != len(tree.nodes):
            old = len(tree.nodes)

            for (n, d) in list(tree.degree()):
                if d == 1 and n not in steiner.terminals:
                    tree.remove_node(n)

        return tree, sum(d for (u, v, d) in tree.edges(data='weight'))

    def vertex_insertion(self, steiner):
        for n in steiner.graph.nodes:
            if not self.tree.has_node(n):
                # Find neighbors that are in the solution
                nb = [x for x in steiner.graph.neighbors(n) if self.tree.has_node(x)]

                # With only one intersecting neighbor there is no chance of improvement
                if len(nb) > 1:
                    g = self.tree.copy()

                    # Add first edge
                    g.add_edge(n, nb[0], weight=steiner.graph[n][nb[0]]['weight'])

                    # Try to insert edges and improve result
                    for i in xrange(1, len(nb)):
                        c = steiner.graph[n][nb[i]]['weight']
                        p = list(dijkstra_path(g, n, nb[i]))

                        # Find most expensive edge in path
                        c_max = (None, None, 0)
                        for j in xrange(1, len(p)):
                            c_prime = g[p[j-1]][p[j]]['weight']

                            if c_prime > c_max[2]:
                                c_max = (p[j-1], p[j], c_prime)

                        # If more expensive than the edge we want to insert, try
                        if c_max[2] > c:
                            g.add_edge(n, nb[i], weight=c)
                            g.remove_edge(c_max[0], c_max[1])

                    # Check if the new result is cheaper
                    new_cost = sum((d for (u, v, d) in g.edges(data='weight')))
                    if new_cost < self.cost:
                        self.cost = new_cost
                        self.tree = g

    def path_exchange(self, steiner, favor_new):
        if len(self.tree.nodes) < 5:
            return

        bridges = {}

        # Find voronoi regions
        for n in self.tree.nodes:
            bridges[n] = []

        vor = VoronoiPartition(steiner.graph, self.tree)

        # Find bridging edges
        for (u, v, d) in steiner.graph.edges(data='weight'):
            t1 = vor._closest[u]
            t2 = vor._closest[v]

            if t1 != t2:
                cost = d + vor.regions[t1][u][0] + vor.regions[t2][v][0]
                bridges[t1].append([cost, (u, v, d)])
                bridges[t2].append([cost, (u, v, d)])

        for k, e in bridges.items():
            e.sort(key=lambda x: x[0])

        # Critical nodes
        key_nodes = set((x for x in self.tree.nodes if x in steiner.terminals or self.tree.degree(x) > 2))

        # DFS into the tree
        root = next(iter(steiner.terminals))
        c_path = []

        # Work on a copy
        g_prime = self.tree.copy()

        forbidden = set()
        pinned = set()

        def path_exchange_rec(node, last, parent):
            c_path.append(node)
            new_last = node if node in key_nodes else last

            subset = set()
            for n2 in self.tree.neighbors(node):
                if n2 != parent:
                    [subset.add(x) for x in (path_exchange_rec(n2, new_last, node))]

            # Remove self from path
            c_path.pop()

            subset.add(node)

            # Is start of a key path and not the root?
            if node in key_nodes and parent is not None:

                # Find intermediary nodes and cost of the current key path
                intermediaries = set()
                idx = len(c_path) - 1
                c_path_cost = steiner.graph[node][parent]['weight']
                while c_path[idx] != last:
                    intermediaries.add(c_path[idx])
                    c_path_cost += steiner.graph[c_path[idx]][c_path[idx - 1]]['weight']
                    idx -= 1

                # Do not try to remove pinned elements
                if any((x in pinned for x in intermediaries)):
                    return subset

                # "Repair" Voronoi, i.e. assign the nodes associated with the intermediaries to new nodes
                vor.repair(intermediaries)

                min_bound = (maxint, None, None, None)
                while True and len(bridges[node]) > 0:
                    c_cost, (x, y, dist) = bridges[node][0]
                    u_in = any(x in vor.regions[n2] for n2 in subset)
                    v_in = any(y in vor.regions[n2] for n2 in subset)
                    u_in = u_in or any(x in vor._tmp_regions[n2] for n2 in subset)
                    v_in = v_in or any(y in vor._tmp_regions[n2] for n2 in subset)
                    u_in = u_in or (x in intermediaries)
                    v_in = v_in or (y in intermediaries)

                    if u_in and v_in:
                        bridges[node].pop(0)
                    else:
                        p1 = vor.extract_path(x)
                        p2 = vor.extract_path(y)

                        if p1[1] not in forbidden and p2[1] not in forbidden:
                            min_bound = (c_cost, (x, y, dist), p1, p2)
                        break

                # Find cheapest edge in intermediaries
                # Since the bridge values calculations do not match anymore, search all
                for p in intermediaries:
                    for c, (x, y, dist) in bridges[p]:
                        u_in = any(x in vor.regions[n2] for n2 in subset)
                        v_in = any(y in vor.regions[n2] for n2 in subset)
                        u_in = u_in or any(x in vor._tmp_regions[n2] for n2 in subset)
                        v_in = v_in or any(y in vor._tmp_regions[n2] for n2 in subset)

                        if u_in ^ v_in:
                            total_cost = vor.dist(x) + vor.dist(y) + dist
                            if total_cost < min_bound[2]:
                                p1 = vor.extract_path(x)
                                p2 = vor.extract_path(y)

                                if p1[1] not in forbidden and p2[1] not in forbidden:
                                    min_bound = (total_cost, (x, y, dist), p1, p2)

                # Found a better key path. Favor new tries tries to establish a new path to change the tree
                if min_bound[0] < c_path_cost or (favor_new and min_bound[0] == c_path_cost):
                    idx = len(c_path) - 1
                    g_prime.remove_edge(parent, node)

                    while c_path[idx] != last:
                        g_prime.remove_edge(c_path[idx], c_path[idx - 1])
                        idx -= 1

                    # Add new path
                    for (x, y, dist) in min_bound[2][0]:
                        g_prime.add_edge(x, y, weight=dist)
                    for (x, y, dist) in min_bound[3][0]:
                        g_prime.add_edge(x, y, weight=dist)

                    (x, y, dist) = min_bound[1]
                    g_prime.add_edge(x, y, weight=dist)

                    # Remove intermediaries, if orphaned
                    [g_prime.remove_node(x) for x in intermediaries if g_prime.degree[x] == 0]

                    # Add descendants and intermediaries as forbidden
                    [forbidden.add(x) for x in subset]
                    [forbidden.add(x) for x in intermediaries]

                    # Add endpoints as pinned
                    pinned.add(min_bound[2][1])
                    pinned.add(min_bound[3][1])

                # Merge bridge list with parent
                bridges[last] = list(merge(bridges[last], bridges[node]))
                for p in intermediaries:
                    bridges[last] = list(merge(bridges[last], bridges[p]))

                vor.reset()

            return subset

        # Start progressing down the tree
        path_exchange_rec(root, root, None)

        self.tree = g_prime
        self.cost = sum([d for (u, v, d) in g_prime.edges(data='weight')])

    def keyvertex_deletion(self, steiner):
        if len(self.tree.nodes) < 3:
            return

        bridges = {}
        horizontal = {}

        # Pick root and create directed tree
        root = next(iter(steiner.terminals))
        d_tree = dfs_tree(self.tree, root)

        forbidden = set()
        pinned = set()

        # Find voronoi regions
        for n in self.tree.nodes:
            bridges[n] = []
            horizontal[n] = []

        vor = VoronoiPartition(steiner.graph, self.tree)

        # Find bridging edges and horizontal edges
        for (u, v, d) in steiner.graph.edges(data='weight'):
            t1 = vor.closest(u)
            t2 = vor.closest(v)

            if t1 != t2:
                cost = d + vor.regions[t1][u][0] + vor.regions[t2][v][0]
                bridges[t1].append([cost, (u, v, d)])
                bridges[t2].append([cost, (u, v, d)])

                # Find lowest common ancestor
                anc = ancestors(d_tree, t1)
                anc.add(t1)
                c_n = t2
                while c_n not in anc:
                    c_n = d_tree.predecessors(c_n).next()

                # If one the nodes is itself the nca, the edge is not horizontal
                if c_n != t1 and c_n != t2:
                    horizontal[c_n].append((u, v, d))

        for k, e in bridges.items():
            e.sort(key=lambda x: x[0])

        critical_nodes = set((x for x in self.tree.nodes if x in steiner.terminals or self.tree.degree(x) > 2))

        def kv_rec(node, last):
            new_last = node if node in critical_nodes else last

            # DFS
            child_solutions = []
            for n2 in d_tree.neighbors(node):
                child_solutions.append(kv_rec(n2, new_last))

            # Non-Key?
            if node in steiner.terminals or len(child_solutions) <= 1:
                # Move border nodes up
                if node != root:
                    parent = d_tree.predecessors(node).next()
                    bridges[parent] = list(merge(bridges[parent], bridges[node]))

                # If terminal, node is critical. Therefore update subset and clear intermediary list
                if node in steiner.terminals:
                    subset = set()
                    subset.add(node)

                    for (ss, inter, lst) in child_solutions:
                        [subset.add(x) for x in ss]
                        [subset.add(x) for x in inter]

                    return subset, [], node
                # Otherwise add self to intermediary list
                else:
                    child_solutions[0][1].append(node)
                    return child_solutions[0]
            # Key?
            else:
                parent_intermediaries = set()
                if node == root:
                    parent_path = []
                else:
                    c_node = d_tree.predecessors(node).next()
                    parent_path = [(node, c_node)]
                    while c_node != last:
                        parent_intermediaries.add(c_node)
                        nxt = d_tree.predecessors(c_node).next()
                        parent_path.append((nxt, c_node))
                        c_node = nxt

                # Create list of intermediaries. Treat current node as such and "repair" voronoi
                child_intermediaries = set(x for l in child_solutions for x in l[1])
                child_subsets = dict((tn, ss) for ss, se, tn in child_solutions)
                intermediaries = parent_intermediaries.union(child_intermediaries)
                intermediaries.add(node)

                subsets = set(chain.from_iterable((ss for kv, ss in child_subsets.items())))
                [subsets.add(x) for x in intermediaries]
                subsets.add(node)

                # Do not remove pinned
                if any(x in pinned for x in intermediaries):
                    return subsets, [], node

                vor.repair(intermediaries)

                # Use valid (i.e. not ending in an intermediary area) horizontal edges
                candidate_edges = []
                for (x, y, dist) in horizontal[node]:
                    violated = any(x in vor.regions[l] for l in child_intermediaries)
                    violated = violated or any(y in vor.regions[l] for l in child_intermediaries)

                    if not violated:
                        candidate_edges.append((x, y, dist))

                # Clean boundary edges
                for c_child, c_ss in child_subsets.items():
                    while len(bridges[c_child]) > 0:
                        total, (x, y, dist) = bridges[c_child][0]
                        # Select those edges where one endpoint is below node and one is above (i.e. not between)
                        x_sub = any(x in vor.regions[t] for t in c_ss)
                        y_sub = any(y in vor.regions[t] for t in c_ss)
                        x_int = any(x in vor.regions[t] for t in intermediaries)
                        y_int = any(y in vor.regions[t] for t in intermediaries)

                        # not (y_int or y_sub) means y is in top partition
                        if not ((x_sub and not (y_int or y_sub)) or (y_sub and not (x_int or x_sub))):
                            bridges[c_child].pop(0)
                        else:
                            candidate_edges.append((x, y, dist))
                            break

                def find_component(target_node):
                    cp = [cpt for (cpt, ss) in child_subsets.items() if target_node in ss]
                    cp = cp[0] if len(cp) > 0 else last
                    return cp

                # Check intermediary bridges
                for c_int in intermediaries:
                    for total, (x, y, dist) in bridges[c_int]:
                        c1 = find_component(vor.closest(x))
                        c2 = find_component(vor.closest(y))
                        if c1 != c2:
                            candidate_edges.append((x, y, dist))

                # Ok now we have all potential edges, calculate the MST
                shortest_edges = dict()

                # Find shortest paths
                for (x, y, dist) in candidate_edges:
                    # Find voronoi center
                    tp1 = vor.closest(x)
                    tp2 = vor.closest(y)

                    # Find component
                    c1 = find_component(tp1)
                    c2 = find_component(tp2)

                    if c1 > c2:
                        c1, c2 = c2, c1

                    total_cost = vor.dist(x) + vor.dist(y) + dist
                    # It may happen that c1 == c2 since the edges in bridges[last] have not been cleaned up
                    if (c1, c2) not in shortest_edges or shortest_edges[(c1, c2)][0] > total_cost:
                        p1 = vor.extract_path(x)
                        p2 = vor.extract_path(y)

                        if p1[1] not in forbidden and p2[1] not in forbidden:
                            shortest_edges[(c1, c2)] = (total_cost, (x, y, dist), p1, p2)

                # Create graph to calculate mst
                super_graph = Graph()
                [super_graph.add_edge(tp1, tp2, weight=total) for ((tp1, tp2), (total, edge, p1, p2)) in shortest_edges.items()]

                # Check if any node is not possibly connected
                if all(super_graph.has_node(x) for x in child_subsets.keys()) and super_graph.has_node(last):
                    mst_edges = list(minimum_spanning_edges(super_graph))
                    mst_cost = sum((dist['weight'] for (x, y, dist) in mst_edges))

                    # Calculate original cost
                    child_edges = list(parent_path)
                    for (ss, pth, src) in child_solutions:
                        c_node = src
                        for idx in range(0, len(pth)):
                            nxt = pth[idx]
                            child_edges.append((c_node, nxt))
                            c_node = nxt

                        child_edges.append((c_node, node))

                    original_cost = sum(steiner.graph[x][y]['weight'] for (x, y) in child_edges)

                    # Replace
                    if original_cost > mst_cost:
                        [self.tree.remove_edge(x, y) for (x, y) in child_edges]

                        for (x, y, dist) in mst_edges:
                            if x > y:
                                x, y = y, x

                            total, (xp, yp, dp), p1, p2 = shortest_edges[(x, y)]
                            self.tree.add_edge(xp, yp, weight=dp)
                            [self.tree.add_edge(cu, cv, weight=cd) for cu, cv, cd in p1[0]]
                            [self.tree.add_edge(cu, cv, weight=cd) for cu, cv, cd in p2[0]]

                            # Mark path endpoints
                            pinned.add(p1[1])
                            pinned.add(p2[1])

                        # Remove orphaned
                        [self.tree.remove_node(x) for x in intermediaries if self.tree.degree[x] == 0]

                        [forbidden.add(x) for x in subsets]
                        [forbidden.add(x) for x in intermediaries]

                vor.reset()

                # Update node boundary. This is a cleanup task for after the iteration, but since we may return

                for kv in child_subsets.keys():
                    bridges[node] = merge(bridges[node], bridges[kv])
                for kv in child_intermediaries:
                    bridges[node] = merge(bridges[node], bridges[kv])

                bridges[node] = list(bridges[node])

                return subsets, [], node

        kv_rec(root, root)
        self.cost = sum(d for (u, v, d) in self.tree.edges(data='weight'))

    def get_descendants(self, g):
        """Produces a dictionary for each node in the tree, containing the terminals preceding the node"""
        if self._descendants is not None:
            return self._descendants

        self._descendants = {}

        # DFS
        queue = [(self.get_root(g), {self.get_root(g)})]

        while len(queue) > 0:
            n, s = queue.pop()

            self._descendants[n] = set()
            if n in g.terminals:
                for n2 in s:
                    self._descendants[n2].add(n)
                self._descendants[n].add(n)

            s2 = set(s)
            s2.add(n)
            for n2 in self.tree.neighbors(n):
                if n2 not in s:
                    queue.append((n2, s2))

        return self._descendants
