import networkx as nx
from sys import maxint
import steiner_approximation as sa
from collections import defaultdict
from heapq import heappop, heappush


class SteinerGraph:
    """Data structure that stores an instance. I.e. a graph and terminals. Offers several helping methods"""

    def __init__(self):
        self.graph = nx.Graph()
        self.terminals = set()
        self._closest_terminals = None
        self._lengths = {}
        self._steiner_lengths = None
        self._approximation = None
        self._voronoi_areas = None
        self._radius = None
        self._restricted_lengths = {}
        self._restricted_closest = None
        self.lower_bound = 0

        self._dist_validity = -2
        self._steiner_validity = -2
        self._approx_validity = -2
        self._restricted_validity = -2

    def add_edge(self, n1, n2, c):
        """Adds an edge to the graph. Distances are updated in case it replaces the same edge with higher costs."""
        if self.graph.has_edge(n1, n2):
            orig = self.graph[n1][n2]['weight']
            # Exists, but existing is more expensive
            if orig > c:
                self.graph[n1][n2]['weight'] = c
                return True
            # Cheaper edge exists
            else:
                return False

        # Non-existing, simply add. This method
        self.graph.add_edge(n1, n2, weight=c)
        return True

    def remove_edge(self, u, v):
        self.graph.remove_edge(u, v)

        if self.graph.degree[u] == 0:
            self.remove_node(u)
        if self.graph.degree[v] == 0:
            self.remove_node(v)

    def _reset_lengths(self):
        self._lengths = {}
        self._closest_terminals = None
        self._voronoi_areas = None
        self._dist_validity = 0
        self._radius = None

    def get_lengths(self, n1, n2=None):
        """Retrieve the length of the shortest path between n1 and n2. If n2 is empty all paths from n1 are returned"""
        if self._dist_validity == -2:
            self._reset_lengths()

        if n1 not in self._lengths:
            # If non-existing try the other way round. If still not existing calculate
            if n2 is not None and n2 in self._lengths:
                return self._lengths[n2][n1]
            else:
                self._lengths[n1] = nx.single_source_dijkstra_path_length(self.graph, n1)

        # If n2 is empty return the distances to all other nodes
        if n2 is None:
            return self._lengths[n1]

        return self._lengths[n1][n2]

    def get_approximation(self):
        """ Returns an approximation that can be used as an upper bound"""
        if self._approximation is None or self._approx_validity != 0:
            self._approximation = sa.SteinerApproximation(self)

        self._approx_validity = 0

        return self._approximation

    def calculate_steiner_length(self):
        self._steiner_lengths = {}
        g = nx.Graph()

        [g.add_edge(t1, t2, weight=self.get_lengths(t1, t2))
         for t1 in self.terminals for t2 in self.terminals if t2 > t1]

        mst = nx.minimum_spanning_tree(g)

        for (t1, t2) in [(t1, t2) for t1 in self.terminals for t2 in self.terminals if t2 > t1]:
            p = nx.shortest_path(mst, t1, t2)
            max_l = 0
            for i in xrange(1, len(p)):
                max_l = max(max_l, g[p[i-1]][p[i]]['weight'])

            self._steiner_lengths.setdefault(t1, {})[t2] = max_l

        self._steiner_validity = 0

    # TODO: Use bound
    def get_steiner_lengths(self, n1, n2, bound):
        if self._steiner_lengths is None or self._steiner_validity == -2:
            self.calculate_steiner_length()
            self._voronoi_areas = None
            self._closest_terminals = None

        if n1 > n2:
            n1, n2 = n2, n1

        # The distances to the closest terminal are a lower bound
        cls1 = self.get_closest(n1)
        cls2 = self.get_closest(n2)

        # Current bound is the edge length (if it exists)
        sd = self.graph[n1][n2]['weight'] if self.graph.has_edge(n1, n2) else maxint
        closest1 = [cls1[0]] if n1 in self.terminals \
            else [cls1[i] for i in xrange(min(3, len(self.terminals))) if cls1[i][1] < sd]
        closest2 = [cls2[0]] if n2 in self.terminals \
            else [cls2[i] for i in xrange(min(3, len(self.terminals))) if cls2[i][1] < sd]

        if len(closest1) == 0 or len(closest2) == 0:
            return sd

        for ct1 in closest1:
            for ct2 in closest2:
                val = max(ct1[1], ct2[1])

                if ct1[0] == ct2[0]:
                    sd = min(sd, val)
                else:
                    t1 = min(ct1[0], ct2[0])
                    t2 = max(ct1[0], ct2[0])
                    sd = min(sd, max(val, self._steiner_lengths[t1][t2]))

        return sd

    def path_contains(self, n1, n2, u, v, c):
        path_dist = self.get_lengths(n1, n2)
        dist1 = self.get_lengths(n2, v) + c + self.get_lengths(u, n1)
        dist2 = self.get_lengths(n1, v) + c + self.get_lengths(u, n2)

        dist = min(dist1, dist2)

        if path_dist == dist:
            return True

        return False

    def contract_edge(self, u, v):
        ret = []
        # Contract
        for ng in nx.neighbors(self.graph, v):
            if ng != u:
                d = self.graph[v][ng]['weight']
                if self.add_edge(u, ng, d):
                    ret.append(((u, ng, d), (v, ng, d)))

        if v in self.terminals:
            self.move_terminal(v, u)

        self.remove_node(v)

        return ret

    def remove_node(self, n):
        if self.graph.has_node(n):
            self.graph.remove_node(n)

        self._lengths.pop(n, None)
        if self._voronoi_areas is not None:
            self._voronoi_areas.pop(n, None)

        if n in self.terminals:
            self.terminals.remove(n)

    def move_terminal(self, t_source, t_target):
        if self._dist_validity == -2:
            self._reset_lengths()

        self.terminals.remove(t_source)

        if self._closest_terminals is not None:
            for i in xrange(0, len(self._closest_terminals)):
                if self._closest_terminals[i] is not None:
                    if self.graph.has_node(i):
                        self._closest_terminals[i] = [x for x in self._closest_terminals[i] if x[0] != t_source]
                        if t_target not in self.terminals:
                            self._closest_terminals[i].append((t_target, self.get_lengths(t_target, i)))
                            self._closest_terminals[i].sort(key=lambda xx: xx[1])
                    else:
                        self._closest_terminals[i] = None

        if self._restricted_closest is not None and self._restricted_validity != -2:
            for i in xrange(0, len(self._restricted_closest)):
                if self._restricted_closest[i] is not None:
                    # Do not forget this is a list, not a dictionary, i.e. entries for non-nodes exist
                    if self.graph.has_node(i):
                        self._restricted_closest[i] = [x for x in self._restricted_closest[i] if x[0] != t_source]
                        if t_target not in self.terminals:
                            self._restricted_closest[i].append((t_target, self.get_restricted(t_target, i)))
                            self._restricted_closest[i].sort(key=lambda e: e[1])
                    else:
                        self._restricted_closest[i] = None

        if t_target not in self.terminals:
            self.terminals.add(t_target)

            if self._voronoi_areas is not None:
                self._voronoi_areas[t_target] = set()

        if self._voronoi_areas is not None:
            for n in self._voronoi_areas[t_source]:
                self._voronoi_areas[t_target].add(n)
            self._voronoi_areas.pop(t_source, None)

            for (k, v) in self._voronoi_areas.items():
                if t_target in v:
                    v.remove(t_target)

    def get_voronoi(self):
        if self._dist_validity == -2:
            self._reset_lengths()

        if self._voronoi_areas is None:
            self._voronoi_areas = {}
            for t in self.terminals:
                self._voronoi_areas[t] = set()

            for n in nx.nodes(self.graph):
                if n not in self.terminals:
                    min_val = maxint
                    min_node = None

                    for t in self.terminals:
                        c = self.get_lengths(t, n)

                        if c < min_val:
                            min_val = c
                            min_node = t

                    self._voronoi_areas[min_node].add(n)

        return self._voronoi_areas

    def get_closest(self, n):
        if self._dist_validity == -2:
            self._reset_lengths()

        if self._closest_terminals is None:
            max_node = max(nx.nodes(self.graph))
            self._closest_terminals = list([None] * (max_node + 1))

        if self._closest_terminals[n] is None:
            self._closest_terminals[n] = [(t, self.get_lengths(t, n)) for t in self.terminals]
            self._closest_terminals[n].sort(key=lambda x: x[1])

        return self._closest_terminals[n]

    def get_radius(self):
        if self._dist_validity == -2:
            self._reset_lengths()

        # This can be included into voronoi generation for efficiency. It is not for readability
        if self._radius is None:
            vor = self.get_voronoi()
            radius_tmp = defaultdict(lambda: maxint)

            for t, l in vor.items():
                for t2 in self.terminals:
                    if t2 != t:
                        radius_tmp[t2] = min(radius_tmp[t2], self.get_lengths(t2, t))
                        for n in l:
                            radius_tmp[t2] = min(radius_tmp[t2], self.get_lengths(t2, n))

            self._radius = [(y, x) for (x, y) in radius_tmp.items()]
            self._radius.sort(key=lambda tup: tup[0])

        return self._radius

    def get_restricted(self, t, n):
        if self._restricted_validity == -2:
            self.find_restricted_closest()

        return self._restricted_lengths[t][n]

    def find_restricted_closest(self):
        max_node = max(n for n in self.graph.nodes) + 1
        self._restricted_closest = [[] for _ in range(0, (max_node + 1))]
        self._restricted_lengths = {t: [maxint] * max_node for t in self.terminals}
        closest = self._restricted_closest
        restricted = self._restricted_lengths
        queue = [(0, t, t) for t in self.terminals]

        push = heappush
        pop = heappop
        nb = self.graph._adj
        done = set()

        while queue:
            dist, n, t = pop(queue)

            if (t, n) in done:
                continue
            done.add((t, n))

            restricted[t][n] = dist
            closest[n].append((t, dist))

            for n2, dta in nb[n].items():
                tot = dist + dta['weight']
                if tot < restricted[t][n2]:
                    restricted[t][n2] = tot

                    if n2 not in self.terminals:
                        push(queue, (tot, n2, t))

        # Add default entries since not every node reaches every terminal
        for l in closest:
            l.extend([(0, maxint) for _ in range(0, len(self.terminals) - len(l))])

        self._restricted_validity = 0

    def get_restricted_closest(self, n):
        if self._restricted_validity == -2:
            self.find_restricted_closest()

        return self._restricted_closest[n]

    def invalidate_dist(self, direction):
        if self._dist_validity == 0:
            self._dist_validity = direction
        elif (self._dist_validity < 0 and direction > 0) or (self._dist_validity > 0 and direction < 0):
            self._dist_validity = -2

        if self._restricted_validity == 0:
            self._restricted_validity = direction
        elif (self._restricted_validity < 0 and direction > 0) or (self._restricted_validity > 0 and direction < 0):
            self._restricted_validity = -2

    def invalidate_steiner(self, direction):
        if self._steiner_validity == 0:
            self._steiner_validity = direction
        elif (self._steiner_validity < 0 and direction > 0) or (self._steiner_validity > 0 and direction < 0):
            self._steiner_validity = -2

    def invalidate_approx(self, direction):
        if self._approx_validity == 0:
            self._approx_validity = direction
        elif (self._approx_validity < 0 and direction > 0) or (self._approx_validity > 0 and direction < 0):
            self._approx_validity = -2

    def requires_dist(self, direction):
        if direction == 0 and self._dist_validity != 0:
            self._dist_validity = -2
        # I.e. either dir is positive and validity negative or the other way round
        elif direction * self._dist_validity < 0:
            self._dist_validity = -2

    def requires_steiner_dist(self, direction):
        if direction == 0 and self._steiner_validity != 0:
            self._steiner_validity = -2
        elif direction * self._steiner_validity < 0:
            self._steiner_validity = -2

    def requires_approx(self, direction):
        if direction == 0 and self._approx_validity != 0:
            self._approx_validity = -2
        elif direction * self._approx_validity < 0:
            self._approx_validity = -2

    def requires_restricted_dist(self, direction):
        if direction == 0 and self._restricted_validity != 0:
            self._restricted_validity = -2
        elif direction * self._restricted_validity < 0:
            self._restricted_validity = -2

    def reset_all(self):
        if self._approx_validity != 0:
            self._approx_validity = -2

        if self._dist_validity != 0:
            self._dist_validity = -2

        if self._steiner_validity != 0:
            self._steiner_validity = -2

        if self._restricted_validity != 0:
            self._restricted_validity = -2
