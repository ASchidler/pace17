from sys import maxint
import heapq as hq
from networkx import single_source_dijkstra_path_length, single_source_dijkstra_path, is_connected
import steiner_graph as sg
import steiner_approximation as sa
from reduction import degree, long_edges, ntdk, sdc, terminal_distance
from preselection import short_links, nearest_vertex
from reducer import Reducer
import time


class DualAscent:
    def __init__(self, run_once=False):
        self.runs = 0
        self._done = False
        self._run_once = run_once

    def reduce(self, steiner, cnt, last_run):
        # This invalidates the approximation. This is important in case the DA doesnt go through in the last run
        # so the solver has a valid approximation
        steiner.invalidate_approx(-2)

        if len(steiner.terminals) < 4 or (self._run_once and self.runs > 0):
            return 0

        small_graph = len(steiner.graph.nodes) < 500 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 3

        da_limit = 10 if len(steiner.graph.edges) / len(steiner.graph.nodes) <= 10 else 1

        if self.runs > 0 and cnt > 0 and not last_run:
            return 0

        self.runs += 1
        ts = list(steiner.terminals)
        track = len(steiner.graph.edges)
        results = []

        # Spread chosen roots a little bit, as they are usually close
        num_results = min(da_limit, len(ts))
        target_roots = (ts[max(len(ts) / num_results, 1) * i] for i in xrange(0, num_results))

        for root in target_roots:
            bnd, grph = self.calc(steiner, root)
            results.append((bnd, root, grph))

        results.sort(key=lambda x: x[0], reverse=True)
        max_result, max_root, max_graph = results[0]

        idx_list = [[0, 1], [2, 3], [4, 5], [0, 1, 2], [0, 3, 5], [0, 1, 2, 3], [0, 1, 2, 3, 4]]
        # idx_list = [[0, 1], [2, 3], [0, 1, 2, 3, 4]]
        aps = [self.find_new(steiner, [results[i] for i in idx]) for idx in idx_list]
        new_ap2 = min(aps, key=lambda x: x.cost)
        #new_ap2 = self.find_new(steiner, results)

        if new_ap2.cost < steiner.get_approximation().cost:
            steiner._approximation = new_ap2

        if small_graph:
            pruned_list = [self.prune_ascent(steiner, results[i]) for i in range(0, min(len(results), 5))]
            for x in pruned_list:
                if x.cost < steiner.get_approximation().cost:
                    steiner._approximation = x

            idx_list = [[0, 1], [2, 3], [0, 4], [0, 1, 2], [0, 3, 4], [0, 1, 2, 3], [0, 1, 2, 3, 4]]
            comb = [self.find_new_from_sol(steiner, [pruned_list[i] for i in idx]) for idx in idx_list]
            for c_comb in comb:
                if c_comb.cost < steiner.get_approximation().cost:
                    steiner._approximation = c_comb
            # comb = self.find_new_from_sol(steiner, pruned_list)
            # if comb.cost < steiner.get_approximation().cost:
            #     steiner._approximation = comb
        else:
            pruned = self.prune_ascent(steiner, results[0])
            if pruned.cost < steiner.get_approximation().cost:
                steiner._approximation = pruned

        if small_graph:
            for c_bnd, c_root, c_g in results:
                self.reduce_graph(steiner, c_g, c_bnd, c_root)
        else:
            self.reduce_graph(steiner, max_graph, max_result, max_root)

        DualAscent.root = max_root
        DualAscent.graph = max_graph
        DualAscent.value = max_result

        track = track - len(steiner.graph.edges)
        if track > 0:
            steiner.invalidate_steiner(-2)
            steiner.invalidate_dist(-2)

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

    def prune_ascent(self, steiner, result):
        og = sg.SteinerGraph()
        bnd, r, g = result

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

                    else:
                        for n2, dta in nb[n].items():
                            # Do not disconnect tree
                            if not tree.has_edge(n, n2) and g.graph.degree(n2) > 1 and g.graph.degree(n) > 1:
                                total = self.calc_edge_weight(g, n, n2, dta['weight'], t_weight)

                                if total > bnd:
                                    g.remove_edge(n, n2)

        if not is_connected(g.graph):
            return None

        g.invalidate_steiner(-2)
        g.invalidate_dist(-2)
        g.invalidate_approx(-2)

        result = sa.SteinerApproximation(g, limit=10)
        return result

    def find_new_from_sol(self, steiner, solutions):
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
        rs = self.reducers()
        alpha = {(u, v): 0 for (u, v) in steiner.graph.edges}
        dg = sg.SteinerGraph()
        dg.terminals = {x for x in steiner.terminals}

        for (bnd, r, g) in results:
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
        voronoi = {t: {} for t in ts}

        queue = [[0, t, t] for t in ts]
        visited = set()

        pred = dg._pred

        while len(visited) != len(dg.nodes):
            el = hq.heappop(queue)

            if el[1] in visited:
                continue

            visited.add(el[1])

            voronoi[el[2]][el[1]] = el[0]

            for n, dta in pred[el[1]].items():
                if n not in visited:
                    d = dta['weight']
                    hq.heappush(queue, [el[0]+d, n, el[2]])

        return voronoi

    @staticmethod
    def calc(steiner, root):
        dg = steiner.graph.to_directed()
        main_cut = set()
        main_cut.add(root)
        bound = 0
        t_cuts = []
        nb = dg._pred

        for t in (t for t in steiner.terminals if t != root):
            c = set()
            c.add(t)
            t_cuts.append([1, c])

        while len(t_cuts) > 0:
            old_size, c_cut = hq.heappop(t_cuts)
            cut_add = set()

            delta = maxint
            for n in c_cut:
                for n2 in dg.predecessors(n):
                    if n2 not in c_cut:
                        delta = min(delta, dg[n2][n]['weight'])

            bound += delta

            remove = False
            i_edges = 0

            for n in c_cut:
                for n2 in dg.predecessors(n):
                    if n2 not in c_cut:
                        i_edges += 1
                        dg[n2][n]['weight'] -= delta

                        if dg[n2][n]['weight'] == 0:
                            # Find connected nodes
                            queue = [n2]
                            connected_nodes = set()
                            while len(queue) > 0:
                                c_node = queue.pop()
                                connected_nodes.add(c_node)

                                for c_p, dta in nb[c_node].items():
                                    if dta['weight'] == 0 and c_p not in connected_nodes:
                                        queue.append(c_p)

                            root_found = root in connected_nodes
                            remove = remove or root_found
                            cut_add.update(connected_nodes)

                            # This loop is probably a huge performance drain...
                            changed = False
                            for i in reversed(range(0, len(t_cuts))):
                                if n in t_cuts[i][1]:
                                    if root_found:
                                        changed = True
                                        t_cuts.pop(i)
                                    else:
                                        t_cuts[i][1].update(connected_nodes)

                            if changed:
                                hq.heapify(t_cuts)

            if not remove:
                c_cut |= cut_add
                hq.heappush(t_cuts, [i_edges, c_cut])

        return bound, dg

    def post_process(self, solution):
        return solution, False

    def reducers(self):
        """Creates the set of reducing preprocessing tests"""
        return [
            degree.DegreeReduction(),
            long_edges.LongEdgeReduction(True),
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
