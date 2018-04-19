from sys import maxint
from heapq import heappop, heappush, heapify
from networkx import single_source_dijkstra_path_length, single_source_dijkstra_path, is_connected
import steiner_graph as sg
import steiner_approximation as sa
from reduction import degree, long_edges, ntdk, sdc
from preselection import short_links, nearest_vertex
from reducer import Reducer


class DualAscent:
    def __init__(self, run_once=False, quick_run=False):
        self.runs = 0
        self._done = False
        self._run_once = run_once
        self._quick_run = quick_run
        self.enabled = True

    def reduce(self, steiner, cnt, last_run):
        # This invalidates the approximation. This is important in case the DA doesnt go through in the last run
        # so the solver has a valid approximation
        steiner.invalidate_approx(-2)

        self.runs += 1
        if len(steiner.terminals) < 4 or (self._run_once and self.runs > 1):
            return 0

        do_quick_run = self._quick_run and self.enabled and self.runs > 1

        if self.runs > 1 and cnt > 0 and not last_run and not do_quick_run:
            return 0

        if not do_quick_run and self._quick_run:
            return 0

        # parameters
        solution_limit = solution_rec_limit = prune_limit = prune_rec_limit = 0

        if self._quick_run:
            solution_limit = 2
            solution_rec_limit = 1
            prune_limit = 0
            prune_rec_limit = 0
        # Very small graph
        elif len(steiner.graph.nodes) < 200 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 5:
            solution_limit = 20
            solution_rec_limit = 10
            prune_limit = 10
            prune_rec_limit = 5
        # Small graph
        elif len(steiner.graph.nodes) < 500 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 3:
            solution_limit = 15
            solution_rec_limit = 5
            prune_limit = 5
            prune_rec_limit = 3
        # Medium
        elif len(steiner.graph.nodes) < 3000 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 3:
            solution_limit = 10
            solution_rec_limit = 5
            prune_limit = 2
            prune_rec_limit = 1
        # Dense graph
        elif len(steiner.graph.edges) / len(steiner.graph.nodes) > 3:
            solution_limit = 1
            solution_rec_limit = 0
            prune_limit = 1
            prune_rec_limit = 0
        # Large, not dense graphs
        else:
            solution_limit = 5
            solution_rec_limit = 3
            prune_limit = 1
            prune_rec_limit = 0

        ts = list(steiner.terminals)
        track = len(steiner.graph.edges)
        solution_limit = min(solution_limit, len(ts))
        target_roots = (ts[max(len(ts) / solution_limit, 1) * i] for i in xrange(0, solution_limit))

        # Generate solutions
        results = [self.calc(steiner, root) for root in target_roots]
        results.sort(key=lambda x: x[0], reverse=True)

        solution_pool = []

        # Tries to recombine solution graphs into a better solution
        if solution_rec_limit > 0:
            solution_rec_idx = list(self.index_generator(0, len(results), 5))
            solution_pool.extend(self.find_new(steiner, [results[i] for i in idx]) for idx in solution_rec_idx)

        # Tries to find better graphs be pruning the solutions
        if prune_limit > 0:
            solution_pool.extend(self.prune_ascent(steiner, results[i]) for i in range(0, min(len(results), prune_limit)))

        # Tries to find better solutions by recombining the solutions found above
        if prune_rec_limit > 0:
            solution_pool.sort(key=lambda tr: tr.cost)
            pruned_idx = self.index_generator(0, min(10, len(solution_pool)), prune_rec_limit)
            solution_pool.extend(self.find_new_from_sol(steiner, [solution_pool[i] for i in idx]) for idx in pruned_idx)

        # Find best upper bound from all solutions
        ub = min(solution_pool, key=lambda tr: tr.cost)
        if ub.cost < steiner.get_approximation().cost:
            steiner._approximation = ub

        # Reduce graph
        for c_bnd, c_g, c_root in results:
            self.reduce_graph(steiner, c_g, c_bnd, c_root)

        DualAscent.value, DualAscent.graph, DualAscent.root = results[0]

        track = track - len(steiner.graph.edges)
        if track > 0:
            steiner.invalidate_steiner(-2)
            steiner.invalidate_dist(-2)

        self.enabled = track > 0 and self.runs > 1
        return track

    def reduce_graph(self, steiner, g, bnd, root):
        if len(steiner.terminals) <= 3:
            return

        root_dist = single_source_dijkstra_path_length(g, root)
        vor = self.voronoi(g, [t for t in steiner.terminals if t != root])

        edges = set()

        limit = steiner.get_approximation().cost - bnd
        for (t, v) in vor.items():
            for (n, d) in v.items():
                if steiner.graph.has_node(n):
                    # Theoretically the paths should be arc-disjoint -> possible tighter bound
                    if root_dist[n] + d > limit:
                        steiner.remove_node(n)
                    else:
                        for n2 in list(steiner.graph.neighbors(n)):
                            if steiner.graph.has_edge(n, n2) and root_dist[n2] + g[n2][n]['weight'] + d > limit:
                                if (n, n2) in edges:
                                    steiner.remove_edge(n, n2)
                                else:
                                    edges.add((n2, n))

    def index_generator(self, start, end, count):
        gap = end - start
        c_count = 1

        while c_count <= count:
            target = max(2, min(gap, gap / c_count + 1))
            yield [start + (i * 83 + c_count) % gap for i in range(0, target)]
            c_count += 1

    def prune_ascent(self, steiner, result):
        og = sg.SteinerGraph()
        bnd, g, r = result

        og.terminals = set(steiner.terminals)
        for (u, v, d) in g.edges(data='weight'):
            if d == 0:
                og.add_edge(u, v, steiner.graph[u][v]['weight'])

        sol = sa.SteinerApproximation(og)
        red = Reducer(self.reducers())

        for i in xrange(0, 3):
            red.reduce(og)

            sol2 = self.prune(og, max(1, len(og.graph.edges)) / 10, sol.tree)
            if sol2 is None:
                break

            red.reset()
            sol2.tree, sol2.cost = red.unreduce(sol2.tree, sol2.cost)

            if sol2.cost < sol.cost:
                sol = sol2

            if len(og.terminals) < 3:
                break

        return sol

    def calc_edge_weight(self, g, u, v, d, tw):
        dist1 = g.get_restricted_closest(u)[0]
        dist2 = g.get_restricted_closest(v)[0]

        if dist1[0] != dist2[0]:
            return d + dist1[1] + dist2[1] + tw
        else:
            d12 = g.get_restricted_closest(u)[1][1]
            d22 = g.get_restricted_closest(v)[1][1]
            if d12 < maxint and d22 < maxint:
                return d + min(dist1[1] + d22, dist2[1] + d12) + tw
            else:
                return d + dist1[1] + dist2[1] + tw

    def prune(self, g, min_removal, tree):
        if len(g.terminals) < 3:
            return sa.SteinerApproximation(g)

        radius = g.get_radius()
        t_weight = sum(radius[i][0] for i in xrange(0, len(g.terminals) - 2))

        # TODO: Make this more efficient
        # Choose bound s.t. we eliminate at least min_removal edges
        edge_weights = [self.calc_edge_weight(g, u, v, d, t_weight) for (u, v, d) in g.graph.edges(data='weight')]
        edge_weights.sort(reverse=True)
        bnd = edge_weights[min(len(edge_weights)-1, min_removal)]
        nb = g.graph._adj

        for n in list(g.graph.nodes):
            # While all terminals must be in the tree, the list of terminals may have changed during preprocessing
            if not tree.has_node(n) and n not in g.terminals:
                dists = g.get_restricted_closest(n)

                if dists[1][1] < maxint:
                    total = dists[0][1] + dists[1][1] + t_weight

                    if total > bnd:
                        g.remove_node(n)

                    # This causes a worse bound (at least for instance 197)
                    # else:
                    #     for n2, dta in nb[n].items():
                    #         # Do not disconnect tree
                    #         if not tree.has_edge(n, n2) and g.graph.degree(n2) > 1 and g.graph.degree(n) > 1:
                    #             total = self.calc_edge_weight(g, n, n2, dta['weight'], t_weight)
                    #
                    #             if total > bnd:
                    #                 g.remove_edge(n, n2)

        if not is_connected(g.graph):
            return None

        g.invalidate_steiner(-2)
        g.invalidate_dist(-2)
        g.invalidate_approx(-2)

        result = sa.SteinerApproximation(g, limit=10)
        return result

    def find_new_from_sol(self, steiner, solutions):
        """Combines (unoptimal) steiner trees into a new solution"""
        red = Reducer(self.reducers())
        alpha = {(u, v): 0 for (u, v) in steiner.graph.edges}
        dg = sg.SteinerGraph()
        dg.terminals = set(steiner.terminals)

        for ct in solutions:
            for (u, v, d) in ct.tree.edges(data='weight'):
                u, v = min(u, v), max(u, v)
                dg.add_edge(u, v, d)
                alpha[(u, v)] += 1

        red.reduce(dg)

        for ((u, v), d) in alpha.items():
            if d > 0 and dg.graph.has_edge(u, v):
                c = dg.graph[u][v]['weight']
                val = min(c-1, d/3)
                alpha[(u, v)] = val
                dg.graph[u][v]['weight'] -= val

        app = sa.SteinerApproximation(dg, False)

        for ((u, v), d) in alpha.items():
            if d > 0 and dg.graph.has_edge(u, v):
                dg.graph[u][v]['weight'] += d
                if app.tree.has_edge(u, v):
                    app.tree[u][v]['weight'] += d

        app.optimize()

        r_result = red.unreduce(app.tree, app.cost)
        app.tree = r_result[0]
        app.cost = r_result[1]

        return app

    def find_new(self, steiner, results):
        """Combines solution graphs into a new solution"""
        rs = self.reducers()
        alpha = {(u, v): 0 for (u, v) in steiner.graph.edges}
        dg = sg.SteinerGraph()
        dg.terminals = {x for x in steiner.terminals}

        for (bnd, g, r) in results:
            # 0 length paths
            pths = single_source_dijkstra_path(g, r, cutoff=1)
            for t in (t for t in steiner.terminals if t != r):
                for i in range(1, len(pths[t])):
                    u, v = min(pths[t][i-1], pths[t][i]), max(pths[t][i-1], pths[t][i])
                    dg.add_edge(u, v, steiner.graph[u][v]['weight'])
                    alpha[(u, v)] += 1

        cnt = 1
        while cnt > 0:
            cnt = 0
            for r in rs:
                cnt += r.reduce(dg, cnt, False)

        for ((u, v), d) in alpha.items():
            if d > 0 and dg.graph.has_edge(u, v):
                c = dg.graph[u][v]['weight']
                val = min(c-1, d/6)
                alpha[(u, v)] = val

                dg.graph[u][v]['weight'] -= val

        app = sa.SteinerApproximation(dg, False)
        for ((u, v), d) in alpha.items():
            if d > 0 and dg.graph.has_edge(u, v):
                dg.graph[u][v]['weight'] += d
                if app.tree.has_edge(u, v):
                    app.tree[u][v]['weight'] += d

        app.optimize()
        c_result = (app.tree, app.cost)

        while True:
            change = False
            for r in rs:
                ret = r.post_process(c_result)
                c_result = ret[0]
                change = change or ret[1]

            if not change:
                break

        app.tree = c_result[0]
        app.cost = c_result[1]
        return app

    @staticmethod
    def voronoi(dg, ts):
        """Builds a voronoi diagram of the nodes in the graph based on bases in ts"""
        voronoi = {t: {} for t in ts}

        queue = [[0, t, t] for t in ts]
        visited = set()

        pred = dg._pred

        while len(visited) != len(dg.nodes):
            el = heappop(queue)

            if el[1] in visited:
                continue

            visited.add(el[1])

            voronoi[el[2]][el[1]] = el[0]

            for n, dta in pred[el[1]].items():
                if n not in visited:
                    d = dta['weight']
                    heappush(queue, [el[0]+d, n, el[2]])

        return voronoi

    @staticmethod
    def calc(steiner, root):
        """ Calculates a lower bound and an updated graph based on the dual ascent alglorithm"""

        dg = steiner.graph.to_directed()
        main_cut = set()
        main_cut.add(root)
        bound = 0
        t_cuts = []
        nb = dg._pred
        pop = heappop
        push = heappush

        # Initial cuts, every terminal for itself, except the root
        for t in (t for t in steiner.terminals if t != root):
            c = set()
            c.add(t)
            t_cuts.append([1, c])

        # Expand cuts up to the root
        while len(t_cuts) > 0:
            # Start with minimal cut
            old_size, c_cut = pop(t_cuts)
            cut_add = set()

            # Find smallest edge and update
            delta = maxint
            for n in c_cut:
                for n2, dta in nb[n].items():
                    if n2 not in c_cut:
                        delta = min(delta, dta['weight'])

            bound += delta

            # Update edges and find all edges with 0 cost
            remove = False
            i_edges = 0
            heap_changed = False

            for n in c_cut:
                for n2, dta in nb[n].items():
                    if n2 not in c_cut:
                        i_edges += 1
                        dta['weight'] -= delta

                        if dta['weight'] == 0:
                            # Find connected nodes
                            queue = [n2]
                            connected_nodes = set()
                            while len(queue) > 0:
                                c_node = queue.pop()
                                connected_nodes.add(c_node)

                                for c_p, c_dta in nb[c_node].items():
                                    if c_dta['weight'] == 0 and c_p not in connected_nodes:
                                        queue.append(c_p)

                            # If we reached the root, we are finished and can remove the cut
                            root_found = root in connected_nodes
                            remove = remove or root_found
                            cut_add.update(connected_nodes)

                            # This loop is probably a huge performance drain...
                            # Update all other cuts that contain this node
                            for i in reversed(range(0, len(t_cuts))):
                                if n in t_cuts[i][1]:
                                    if root_found:
                                        heap_changed = True
                                        t_cuts.pop(i)
                                    else:
                                        t_cuts[i][1].update(connected_nodes)

            # If we haven't reached to root yet, add the updated cut again
            if not remove:
                c_cut |= cut_add
                if heap_changed:
                    t_cuts.append([i_edges, c_cut])
                else:
                    push(t_cuts, [i_edges, c_cut])

            # Reinstante heapness if changed
            if heap_changed:
                heapify(t_cuts)

        # Return the lower bound and the updated graph
        return bound, dg, root

    def post_process(self, solution):
        return solution, False

    def reducers(self):
        """Creates the set of reducing preprocessing tests"""
        return [
            degree.DegreeReduction(),
            long_edges.LongEdgeReduction(False),
            ntdk.NtdkReduction(True),
            sdc.SdcReduction(),
            degree.DegreeReduction(),
            ntdk.NtdkReduction(False),
            degree.DegreeReduction(),
            short_links.ShortLinkPreselection(),
            nearest_vertex.NearestVertex()
        ]


DualAscent.root = None
DualAscent.graph = None
DualAscent.value = None
