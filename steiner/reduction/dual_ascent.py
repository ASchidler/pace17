import networkx as nx
import sys
import heapq as hq


class DualAscent:
    def reduce(self, steiner):
        ts = list(steiner.terminals)
        max_r = (None, None, 0)
        for i in range(0, min(10, len(ts))):
            root = ts[i]

            result = self.calc(steiner, root)
            if result[0] > max_r[2]:
                max_r = (result[1], root, result[0])

        root_dist = nx.single_source_dijkstra_path_length(max_r[0], max_r[1])
        vor = self.voronoi(max_r[0], [t for t in ts if t != max_r[2]])

        track = 0
        edges = set()
        for (t, v) in vor.items():
            for (n, d) in v.items():
                # Theoretically the paths should be arc-disjoint -> possible tighter bound
                bnd = root_dist[n] + d

                if bnd + max_r[2] > steiner.get_approximation().cost:
                    steiner.remove_node(n)
                    track += 1
                else:
                    for n2 in list(nx.neighbors(steiner.graph, n)):
                        if max_r[2] + root_dist[n2] + d + max_r[0][n2][n]['weight'] > steiner.get_approximation().cost:
                            if (n, n2) in edges:
                                track += 1
                                steiner.remove_edge(n, n2)
                            else:
                                edges.add((n2, n))

        return track

    def voronoi(self, dg, ts):
        voronoi = {t: {} for t in ts}

        queue = [[0, t, t] for t in ts]
        visited = set()

        while len(visited) != len(nx.nodes(dg)):
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

    def calc(self, steiner, root):
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
            c_cut = hq.heappop(t_cuts)[1]
            new_cut = set(c_cut)

            delta = sys.maxint
            for n in c_cut:
                for n2 in dg.predecessors(n):
                    if n2 not in c_cut:
                        delta = min(delta, dg[n2][n]['weight'])
            bound += delta

            remove = False
            for n in c_cut:
                for n2 in dg.predecessors(n):
                    if n2 not in c_cut:
                        d = dg[n2][n]['weight']
                        d = max(0, d - delta)
                        dg[n2][n]['weight'] = d

                        if d <= 0:
                            if n2 in main_cut:
                                remove = True
                            else:
                                found = False

                                for i in range(0, len(t_cuts)):
                                    if n2 in t_cuts[i][1]:
                                        new_cut = new_cut.union(t_cuts.pop(i)[1])
                                        hq.heapify(t_cuts)
                                        found = True
                                        break

                                if not found:
                                    new_cut.add(n2)

            if remove:
                main_cut = main_cut.union(new_cut)
            else:
                hq.heappush(t_cuts, [len(new_cut), new_cut])

        return bound, dg

    def post_process(self, solution):
        return solution, False

