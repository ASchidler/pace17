from time import time


class DebugReduction:
    def __init__(self, r):
        self._r = r

    def reduce(self, g, cnt, last_run):
        tm = time()
        cnt = self._r.reduce(g, cnt, last_run)

        print "Reduced {} needing {} in {}" \
            .format(cnt, str(time() - tm), str(self._r.__class__))

        return cnt

    def post_process(self, solution):
        return self._r.post_process(solution)


class Reducer:
    def __init__(self, reducers, threshold=0.0025):
        self._reducers = reducers
        self._threshold = threshold

    def reduce(self, g):
        last_run = False

        while True:
            min_changes = self._threshold * len(g.graph.edges)
            min_n_changes = self._threshold * len(g.graph.nodes)
            n_length = len(g.graph.nodes)
            cnt_changes = 0

            for r in self._reducers:
                if len(g.graph.nodes) > 1:
                    reduced = r.reduce(g, cnt_changes, last_run)
                    cnt_changes = cnt_changes + reduced

            # TODO: Find a better stopping criterion
            min_n_changes = min_changes = 2
            # Use both edge and node changes, as the NTDK may produce nodes although successful
            if cnt_changes <= min_changes and (n_length - len(g.graph.nodes) <= min_n_changes):
                if last_run:
                    break
                last_run = True
            else:
                last_run = False

            g.reset_all()

    def unreduce(self, graph, cost):
        solution = (graph, cost)

        while True:
            change = False
            for r in self._reducers:
                ret = r.post_process(solution)
                solution = ret[0]
                change = change or ret[1]
            if not change:
                break

        return solution

    def reset(self):
        for r in self._reducers:
            r._done = False


class DebugReducer(Reducer):
    def __init__(self, reducers, threshold=0.05):
        new_reducers = [DebugReduction(r) for r in reducers]
        Reducer.__init__(self, new_reducers, threshold)

    def reduce(self, g):
        tm = time()
        cnt_nodes = len(g.graph.nodes)
        cnt_edges = len(g.graph.edges)
        cnt_terminals = len(g.terminals)
        Reducer.reduce(self, g)
        print "{} nodes, {} edges and {} terminals removed " \
            .format(cnt_nodes - len(g.graph.nodes), cnt_edges - len(g.graph.edges),
                    cnt_terminals - len(g.terminals))
        print "Reductions completed in {}".format(time() - tm)

