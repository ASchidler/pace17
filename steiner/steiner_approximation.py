import sys
import networkx as nx
import heapq
from collections import defaultdict


class VoronoiPartition:
    def __init__(self, source, target):
        self.regions = {}
        self.closest = {}
        self.source = source
        self._tmp_regions = defaultdict(lambda: {})
        self._tmp_closest = {}

        queue = []
        visited = set()

        # Find voronoi regions. Initialize with tree nodes as voronoi centers
        for n in nx.nodes(target):
            self.regions[n] = {}
            # Queue format is: cost, current node, original start, previous node
            heapq.heappush(queue, [0, n, n, n])

        node_count = len(nx.nodes(source))
        while len(visited) != node_count:
            el = heapq.heappop(queue)

            if el[1] not in visited:
                visited.add(el[1])
                self.regions[el[2]][el[1]] = (el[0], el[3])
                self.closest[el[1]] = el[2]

                for n in nx.neighbors(source, el[1]):
                    if n not in visited:
                        cost = el[0] + source[el[1]][n]['weight']
                        heapq.heappush(queue, [cost, n, el[2], el[1]])

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

        # Find all nodes in the deleted regions
        for p in intermediaries:
            repair_nodes = repair_nodes.union(self.regions[p].keys())

        # Initialize dijkstra s.t. the boundary nodes are added with the distance to the adjacent center
        for rep in repair_nodes:
            for nb in nx.neighbors(self.source, rep):
                c_closest = self.closest[nb]
                if c_closest not in intermediaries:
                    cost = self.regions[c_closest][nb][0] + self.source[rep][nb]['weight']
                    heapq.heappush(queue, [cost, rep, c_closest, nb])

        # Run dijkstra, limit to dangling nodes
        while len(visited_repair) != len(repair_nodes):
            el = heapq.heappop(queue)
            if el[1] not in visited_repair:
                visited_repair.add(el[1])
                self._tmp_closest[el[1]] = el[2]
                self._tmp_regions.setdefault(el[2], {})[el[1]] = (el[0], el[3])

                for nb in nx.neighbors(self.source, el[1]):
                    if nb not in visited_repair and nb in repair_nodes:
                        cost = el[0] + self.source[el[1]][nb]['weight']
                        heapq.heappush(queue, [cost, nb, el[2], el[1]])

    def extract_path(self, n):
        t = self._tmp_closest[n] if n in self._tmp_closest else self.closest[n]
        vor = self._tmp_regions[t] if t in self._tmp_regions else self.regions[t]

        while n != t:
            # This is the switch from the "new" assignment back into assigned territory
            if n not in vor:
                vor = self.regions[t]

            prev = vor[n][1]
            yield prev, n, self.source[n][prev]['weight']
            n = prev

    def dist(self, n):
        if n in self._tmp_closest:
            return self._tmp_regions[self._tmp_closest[n]][n][0]
        else:
            return self.regions[self.closest[n]][n][0]


class SteinerApproximation:
    """Represents an approximation algorithm for steiner trees for an upper bound. It applies repeated shortest paths"""
    def __init__(self, steiner):
        self.cost = sys.maxint
        self.tree = None

        # TODO: Find a more sophisticated selection strategy?
        limit = min(20, len(steiner.terminals))
        for i in xrange(0, limit):
            result = self.calculate(steiner, max(len(steiner.terminals) / limit, 1) * i)
            if result[1] < self.cost:
                self.cost = result[1]
                self.tree = result[0]

        print "Original {}".format(self.cost)
        self.path_exchange(steiner, False)
        print "PE {}".format(self.cost)
        self.vertex_insertion(steiner)
        print "VI {}".format(self.cost)

    def calculate(self, steiner, start):
        # Solution init
        tree = nx.Graph()
        cost = 0

        # Queue -> all terminals must be in solutions and processed nodes
        queue = sorted(list(steiner.terminals))
        nodes = set()

        # Set start node
        nodes.add(queue.pop(start))

        while len(queue) > 0:
            # Find terminal with minimal distance to tree
            min_val = sys.maxint
            min_t = None
            min_n = None

            for t in queue:
                for n in nodes:
                    c = steiner.get_lengths(t, n)

                    if c < min_val:
                        min_val = c
                        min_t = t
                        min_n = n

            # Add to solution
            nodes.add(min_t)
            queue.remove(min_t)

            # Find shortest path between
            path = nx.dijkstra_path(steiner.graph, min_t, min_n)

            # Now backtrack edges
            prev_n = min_t
            for i in range(1, len(path)):
                current_n = path[i]
                if not tree.has_edge(prev_n, current_n):
                    nodes.add(current_n)
                    w = steiner.graph[prev_n][current_n]['weight']
                    cost = cost + w
                    tree.add_edge(prev_n, current_n, weight=w)

                prev_n = current_n

        # Improve solution by creating an MST and deleting non-terminal leafs
        tree = nx.minimum_spanning_tree(tree)

        # Remove non-terminal leafs
        old = sys.maxint
        while old != len(nx.nodes(tree)):
            old = len(nx.nodes(tree))

            for (n, d) in list(nx.degree(tree)):
                if d == 1 and n not in steiner.terminals:
                    tree.remove_node(n)

        # Calculate cost
        cost = 0
        for (u, v, d) in list(tree.edges(data='weight')):
            cost = cost + d

        return tree, cost

    def vertex_insertion(self, steiner):
        for n in nx.nodes(steiner.graph):
            if not self.tree.has_node(n):
                # Find neighbors that are in the solution
                nb = [x for x in nx.neighbors(steiner.graph, n) if self.tree.has_node(x)]

                # With only one intersecting neighbor there is no chance of improvement
                if len(nb) > 1:
                    g = self.tree.copy()

                    # Add first edge
                    g.add_edge(n, nb[0], weight=steiner.graph[n][nb[0]]['weight'])

                    # Try to insert edges and improve result
                    for i in xrange(1, len(nb)):
                        c = steiner.graph[n][nb[i]]['weight']
                        p = list(nx.dijkstra_path(g, n, nb[i]))

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
        if len(nx.nodes(self.tree)) < 5:
            return

        bridges = {}

        # Find voronoi regions
        for n in nx.nodes(self.tree):
            bridges[n] = []

        vor = VoronoiPartition(steiner.graph, self.tree)

        # Find bridging edges
        for (u, v, d) in steiner.graph.edges(data='weight'):
            t1 = vor.closest[u]
            t2 = vor.closest[v]

            if t1 != t2:
                cost = d + vor.regions[t1][u][0] + vor.regions[t2][v][0]
                bridges[t1].append([cost, (u, v, d)])
                bridges[t2].append([cost, (u, v, d)])

        for k, e in bridges.items():
            e.sort(key=lambda x: x[0])

        # Keynodes
        key_nodes = set((x for x in nx.nodes(self.tree) if x in steiner.terminals or nx.degree(self.tree, x) > 2))

        # DFS into the tree
        root = next(iter(steiner.terminals))
        c_path = []

        # Work on a copy
        g_prime = self.tree.copy()

        def path_exchange_rec(node, last, parent):
            c_path.append(node)
            new_last = node if node in key_nodes else last

            subset = set()
            for n2 in nx.neighbors(self.tree, node):
                if n2 != parent:
                    subset = subset.union((path_exchange_rec(n2, new_last, node)))

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

                # "Repair" Voronoi, i.e. assign the nodes associated with the intermediaries to new nodes
                vor.repair(intermediaries)

                min_bound = (None, None, sys.maxint, None)
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
                        min_bound = (x, y, c_cost, dist)
                        break

                # Find cheapest edge in intermediaries
                # TODO: The costs don't match, i.e. since one of the nodes is no longer in the voronoi region
                # of the intermediary, the distance calculation used in the bridge entries no longer matches...
                # This is also true of the path calculation
                for p in intermediaries:
                    for c, (x, y, dist) in bridges[p]:
                        if c >= min_bound[2]:
                            break
                        else:
                            u_in = any(x in vor.regions[n2] for n2 in subset)
                            v_in = any(y in vor.regions[n2] for n2 in subset)
                            u_in = u_in or any(x in vor._tmp_regions[n2] for n2 in subset)
                            v_in = v_in or any(y in vor._tmp_regions[n2] for n2 in subset)

                            if u_in ^ v_in:
                                min_bound = (x, y, c, dist)
                                break

                # Found a better key path
                if min_bound[2] <= c_path_cost:
                    # Remove old path
                    idx = len(c_path) - 1
                    g_prime.remove_edge(parent, node)
                    while c_path[idx] != last:
                        g_prime.remove_edge(c_path[idx], c_path[idx - 1])
                        idx -= 1

                    p1 = list(vor.extract_path(min_bound[0]))
                    p2 = list(vor.extract_path(min_bound[1]))
                    # Add new path
                    for (x, y, dist) in vor.extract_path(min_bound[0]):
                        g_prime.add_edge(x, y, weight=dist)
                    for (x, y, dist) in vor.extract_path(min_bound[1]):
                        g_prime.add_edge(x, y, weight=dist)

                    g_prime.add_edge(min_bound[0], min_bound[1], weight=min_bound[3])

                    # Remove intermediaries, if orphaned
                    [g_prime.remove_node(x) for x in intermediaries if g_prime.degree[x] == 0]
                if not nx.is_connected(g_prime) or not nx.is_tree(g_prime) or len(
                        [x for x in steiner.terminals if not g_prime.has_node(x)]) > 0:
                    print "Error"

                # Merge bridge list with parent
                bridges[last] = list(heapq.merge(bridges[last], bridges[node]))
                for p in intermediaries:
                    bridges[last] = list(heapq.merge(bridges[last], bridges[p]))

                vor.reset()

            return subset

        # Start progressing down the tree
        path_exchange_rec(root, root, None)

        self.tree = g_prime
        self.cost = sum([d for (u, v, d) in g_prime.edges(data='weight')])
