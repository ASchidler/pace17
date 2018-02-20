

class ZeroEdgeReduction:
    """Reduction that automatically contracts edges with weight 0"""
    def __init__(self):
        self.merged = []

    def reduce(self, steiner):
        cnt = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            if d == 0:
                for e in steiner.contract_edge(u, v):
                    self.merged.append(e)
                cnt = cnt + 1

        return cnt

    def post_process(self, solution):
        change = False

        for (e1, e2) in self.merged:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return solution, change
