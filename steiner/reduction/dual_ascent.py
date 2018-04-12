import networkx as nx
import sys
import heapq as hq


class DualAscent:
    def reduce(self, steiner):
        if len(steiner.terminals) < 4:
            return 0

        ts = list(steiner.terminals)
        max_r = (None, None, 0)
        track = 0

        for i in range(0, min(10, len(ts))):
            root = ts[i]

            result = self.calc(steiner, root)
            if result[0] > max_r[2]:
                max_r = (result[1], root, result[0])

        root_dist = nx.single_source_dijkstra_path_length(max_r[0], max_r[1])
        vor = self.voronoi(max_r[0], [t for t in ts if t != max_r[2]])

        edges = set()
        limit = steiner.get_approximation().cost - max_r[2]
        for (t, v) in vor.items():
            for (n, d) in v.items():
                # Theoretically the paths should be arc-disjoint -> possible tighter bound
                if root_dist[n] + d > limit:
                    steiner.remove_node(n)
                    track += 1
                else:
                    for n2 in list(nx.neighbors(steiner.graph, n)):
                        if root_dist[n2] + max_r[0][n2][n]['weight'] + d > limit:
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
            old_size, c_cut = hq.heappop(t_cuts)
            cut_add = set()

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

                            new_ts = connected_nodes.intersection(steiner.terminals)

                            cut_add.update(connected_nodes)
                            remove = remove or len(new_ts) > 0

                            # This loop is probably a huge performance drain...
                            for i in reversed(range(0, len(t_cuts))):
                                if n in t_cuts[i][1]:
                                    if any(x not in t_cuts[i][1] for x in new_ts):
                                        t_cuts.pop(i)
                                        hq.heapify(t_cuts)
                                    else:
                                        t_cuts[i][1].update(connected_nodes)

            if not remove:
                c_cut |= cut_add
                hq.heappush(t_cuts, [len(c_cut), c_cut])

        return bound, dg

    def post_process(self, solution):
        return solution, False

