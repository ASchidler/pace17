from sys import maxint
import heapq as hq
from networkx import single_source_dijkstra_path_length, Graph
import steiner_graph as sg
import steiner_approximation as sa
import networkx as nx

class DualAscent:

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.terminals) < 4 or cnt > 0 or len(steiner.graph.edges) / len(steiner.graph.nodes) > 10:
            return 0

        ts = list(steiner.terminals)
        max_r = (None, None, 0)
        track = 0

        for i in range(0, min(10, len(ts))):
            root = ts[i]

            result = self.calc(steiner, root)
            if result[0] > max_r[2]:
                max_r = (result[1], root, result[0])

        new_ap = self.approx_sol(steiner, max_r[0])

        root_dist = single_source_dijkstra_path_length(max_r[0], max_r[1])
        vor = self.voronoi(max_r[0], [t for t in ts if t != max_r[1]])

        edges = set()
        steiner._approximation = None
        limit = steiner.get_approximation().cost - max_r[2]
        for (t, v) in vor.items():
            for (n, d) in v.items():
                # Theoretically the paths should be arc-disjoint -> possible tighter bound
                if root_dist[n] + d > limit:
                    steiner.remove_node(n)
                    track += 1
                else:
                    for n2 in list(steiner.graph.neighbors(n)):
                        if root_dist[n2] + max_r[0][n2][n]['weight'] + d > limit:
                            if (n, n2) in edges:
                                track += 1
                                steiner.remove_edge(n, n2)
                            else:
                                edges.add((n2, n))

        DualAscent.root = max_r[1]
        DualAscent.graph = max_r[0]
        DualAscent.value = max_r[2]


        return track

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

                            # new_ts = connected_nodes.intersection(steiner.terminals)
                            # remove = remove or len(new_ts) > 0
                            # cut_add.update(connected_nodes)
                            #
                            # # This loop is probably a huge performance drain...
                            # changed = False
                            # for i in reversed(range(0, len(t_cuts))):
                            #     if n in t_cuts[i][1]:
                            #         if any(x not in t_cuts[i][1] for x in new_ts):
                            #             changed = True
                            #             t_cuts.pop(i)
                            #         else:
                            #             t_cuts[i][1].update(connected_nodes)
                            #
                            # if changed:
                            #     hq.heapify(t_cuts)

            if not remove:
                c_cut |= cut_add
                hq.heappush(t_cuts, [i_edges, c_cut])

        return bound, dg

    def post_process(self, solution):
        return solution, False


DualAscent.root = None
DualAscent.graph = None
DualAscent.value = None
