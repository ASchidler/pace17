import networkx as nx
import sys
import steiner_graph as sg

# https://www.geeksforgeeks.org/bridge-in-a-graph/


class ComponentFinder:
    def __init__(self):
        self.edges = []

    def _find_bridges(self, steiner):
        visited = set()
        low = CmDictionary(sys.maxint)
        disc = CmDictionary(sys.maxint)
        parent = CmDictionary(-1)
        edges = []
        stack = []

        for n in nx.nodes(steiner.graph):
            if n not in visited:
                stack.append(([n], None, True))

                while len(stack) > 0:
                    us, p, t = stack.pop()

                    cnt = 0

                    while len(us) > 0:
                        u = us.pop()
                        if u in visited:
                            if u != parent[p]:
                                low[p] = min(low[p], disc[u])
                            continue

                        cnt += 1
                        parent[u] = p
                        low[u] = len(visited)
                        disc[u] = low[u]
                        visited.add(u)

                        if len(us) > 0:
                            stack.append((us, p, True))

                        new_n = []
                        for v in nx.neighbors(steiner.graph, u):
                            new_n.append(v)
                        stack.append((new_n, u, False))
                        break

                    if cnt == 0 and not t:
                        if len(stack) == 0:
                            target = n
                        else:
                            peek = stack.pop()
                            stack.append(peek)
                            target = peek[1]
                        c_node = p
                        while c_node != target and c_node != n:
                            ux = parent[c_node]
                            vx = c_node
                            low[ux] = min(low[ux], low[vx])

                            if low[vx] > disc[ux]:
                                edges.append((ux, vx))

                            c_node = ux

        return edges

    def decompose(self, steiners):
        result = []

        for steiner in steiners:
            bridges = self._find_bridges(steiner)

            if len(bridges) == 0:
                result.append(steiner)
                continue

            print "{} bridges found".format(len(bridges))

            components = [(steiner.graph, steiner.terminals)]

            for (u, v) in bridges:
                for (c, ts) in components:
                    if c.has_edge(u, v):
                        d = c[u][v]['weight']
                        c.remove_edge(u, v)
                        new_c = list(nx.connected_component_subgraphs(c))
                        if new_c[0].has_node(v):
                            u, v = v, u

                        ts_0 = set()
                        ts_1 = set()
                        for t in ts:
                            if new_c[0].has_node(t):
                                ts_0.add(t)
                            elif new_c[1].has_node(t):
                                ts_1.add(t)

                        if len(ts_0) > 0 and len(ts_0) > 0:
                            ts_0.add(u)
                            ts_1.add(v)
                            self.edges.append((u, v, d))

                        components.remove((c, ts))
                        if len(ts_0) > 0:
                            components.append((new_c[0], ts_0))
                        if len(ts_1) > 0:
                            components.append((new_c[1], ts_1))

                        break

            for (c, t) in components:
                new_graph = sg.SteinerGraph()
                new_graph.graph = c
                new_graph.terminals = t

                result.append(new_graph)

        return result

    def build_solutions(self, results):
        solution = [nx.Graph(), 0]

        for s in results:
            solution[1] += s[1]
            for (u, v, d) in s[0].edges(data='weight'):
                solution[0].add_edge(u, v, weight=d)

        for (u, v, d) in self.edges:
            solution[0].add_edge(u, v, weight=d)
            solution[1] += d

        return solution

class CmDictionary(dict):
    def __init__(self, default):
        self.default = default

    def __missing__(self, key):
        return self.default