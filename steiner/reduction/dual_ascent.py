import networkx as nx
import sys

class DualAscent:
    def reduce(self, steiner):
        ts = list(steiner.terminals)
        max_r = (None, None, 0)
        for i in range(0, min(10, len(ts))):
            root = ts[i]

            result = self.calc(steiner, root)
            if result[0] > max_r[2]:
                max_r = (result[1], root, result[0])

        terminal_dist = {}
        for t in ts:
            terminal_dist[t] = nx.single_source_dijkstra_path_length(max_r[0], t)

        root_dist = terminal_dist.pop(max_r[1])

        track = 0
        for n in nx.nodes(steiner.graph):
            if n not in steiner.terminals:
                bnd = root_dist[n] + min((v[n] for (t, v) in terminal_dist.items()))

                if bnd + max_r[2] > steiner.get_approximation().cost:
                    track += 1

        return track


    def calc(self, steiner, root):
        da_graph = steiner.graph.copy()
        main_cut = set()
        main_cut.add(root)
        cuts = []
        bound = 0

        for t in steiner.terminals:
            if t != root:
                c = set()
                c.add(t)
                cuts.append(c)

        while len(cuts) > 0:
            c_idx = -1
            c_cut = None
            c_min = sys.maxint
            remove = False

            for i in range(0, len(cuts)):
                if len(cuts[i]) < c_min:
                    c_cut = cuts[i]
                    c_idx = i
                    c_min = len(c_cut)

            new_cut = set(c_cut)
            cuts.pop(c_idx)

            delta = sys.maxint
            for n in c_cut:
                for n2 in nx.neighbors(da_graph, n):
                    if n2 not in c_cut:
                        delta = min(delta, da_graph[n][n2]['weight'])

            bound += delta

            for n in c_cut:
                for n2 in nx.neighbors(da_graph, n):
                    if n2 not in c_cut:
                        d = da_graph[n][n2]['weight']
                        d = max(0, d - delta)
                        da_graph[n][n2]['weight'] = d

                        # Add node to cut
                        if d == 0 and n2 not in new_cut:
                            if n2 in main_cut:
                                remove = True
                            else:
                                found = False
                                # Is already in cut?
                                for j in range(0, len(cuts)):
                                    if n2 in cuts[j]:
                                        new_cut = new_cut.union(cuts.pop(j))
                                        found = True
                                        break

                                if not found:
                                    new_cut.add(n2)

            if remove:
                main_cut = main_cut.union(new_cut)
            else:
                cuts.append(new_cut)

        return bound, da_graph

