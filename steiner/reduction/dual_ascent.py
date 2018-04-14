from sys import maxint
import heapq as hq
from networkx import single_source_dijkstra_path_length, Graph
import steiner_graph as sg
import steiner_approximation as sa
import networkx as nx
from reduction import degree, long_edges, ntdk, sdc, terminal_distance
from preselection import short_links, nearest_vertex

class DualAscent:

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.terminals) < 4 or cnt > 0 or len(steiner.graph.edges) / len(steiner.graph.nodes) > 10:
            return 0

        ts = list(steiner.terminals)
        max_r = (None, None, 0)
        track = 0
        results = []
        for i in range(0, min(10, len(ts))):
            root = ts[i]
            bnd, grph = self.calc(steiner, root)
            results.append((bnd, root, grph))

        max_result, max_root, max_graph = max(results, key=lambda x: x[0])

        new_ap = self.approx_sol(steiner, max_graph)
        if new_ap.cost < steiner.get_approximation().cost:
            steiner._approximation = new_ap

        new_ap2 = self.find_new(steiner, results)
        if new_ap2.cost < steiner.get_approximation().cost:
            steiner._approximation = new_ap2

        root_dist = single_source_dijkstra_path_length(max_graph, max_root)
        vor = self.voronoi(max_graph, [t for t in ts if t != max_root])

        edges = set()

        limit = steiner.get_approximation().cost - max_result
        for (t, v) in vor.items():
            for (n, d) in v.items():
                # Theoretically the paths should be arc-disjoint -> possible tighter bound
                # approximate -> Remove root, every node not in a voronoi region -> delete, no route to any other terminal
                if root_dist[n] + d > limit:
                    steiner.remove_node(n)
                    track += 1
                else:
                    for n2 in list(steiner.graph.neighbors(n)):
                        if root_dist[n2] + max_graph[n2][n]['weight'] + d > limit:
                            if (n, n2) in edges:
                                track += 1
                                steiner.remove_edge(n, n2)
                            else:
                                edges.add((n2, n))

        DualAscent.root = max_root
        DualAscent.graph = max_graph
        DualAscent.value = max_result

        return track

    def find_new(self, steiner, results):
        rs = self.reducers()
        alpha = {(u, v): 0 for (u, v) in steiner.graph.edges}
        dg = sg.SteinerGraph()
        dg.terminals = {x for x in steiner.terminals}

        for (bnd, r, g) in results:
            for (u, v, d) in g.edges(data='weight'):
                if d == 0:
                    u, v = min(u, v), max(u, v)
                    dg.add_edge(u, v, steiner.graph[u][v]['weight'])
                    alpha[(u, v)] += 1

        cnt = 1
        while cnt > 0:
            cnt = 0
            for r in rs:
                cnt += r.reduce(dg, cnt, False)

            dg._lengths = {}
            dg._approximation = None
            dg._restricted_lengths = {}
            dg._restricted_closest = None
            dg._radius = None
            dg._voronoi_areas = None

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

    def approx_sol(self, steiner, g):
        ag = sg.SteinerGraph()

        for (u, v, d) in g.edges(data='weight'):
            if d == 0:
                ag.add_edge(u, v, steiner.graph[u][v]['weight'])

        ag.terminals = {x for x in steiner.terminals}

        app = sa.SteinerApproximation(ag)

        return app


    @staticmethod
    def voronoi(dg, ts):
        voronoi = {t: {} for t in ts}

        queue = [[0, t, t] for t in ts]
        visited = set()

        while len(visited) != len(dg.nodes):
            el = hq.heappop(queue)

            if el[1] in visited:
                continue

            visited.add(el[1])

            voronoi[el[2]][el[1]] = el[0]

            for n in dg.predecessors(el[1]):
                if n not in visited:
                    d = dg[n][el[1]]['weight']
                    hq.heappush(queue, [el[0]+d, n, el[2]])

        return voronoi

    @staticmethod
    def calc(steiner, root):
        dg = steiner.graph.to_directed()
        main_cut = set()
        main_cut.add(root)
        bound = 0
        t_cuts = []

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

                                for c_p in dg.predecessors(c_node):
                                    if dg[c_p][c_node]['weight'] == 0 and c_p not in connected_nodes:
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
            terminal_distance.CostVsTerminalDistanceReduction(),
            degree.DegreeReduction(),
            long_edges.LongEdgeReduction(True),
            ntdk.NtdkReduction(True),
            sdc.SdcReduction(),
            degree.DegreeReduction(),
            ntdk.NtdkReduction(False),
            degree.DegreeReduction(),
            terminal_distance.CostVsTerminalDistanceReduction(),
            degree.DegreeReduction(),
        ]


DualAscent.root = None
DualAscent.graph = None
DualAscent.value = None
