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
    def __init__(self, reducers, threshold=0.0025, run_limit=0):
        self._reducers = reducers
        self._threshold = threshold
        self._run_limit = run_limit

    def reduce(self, g):
        last_run = False
        run_num = 1

        while True:
            min_changes = self._threshold * len(g.graph.edges)
            min_n_changes = self._threshold * len(g.graph.nodes)
            n_length = len(g.graph.nodes)
            cnt_changes = 0
            last_run = last_run or (run_num == self._run_limit)

            for r in self._reducers:
                if len(g.graph.nodes) > 1:
                    reduced = r.reduce(g, cnt_changes, last_run)
                    cnt_changes = cnt_changes + reduced

            if cnt_changes <= min_changes and not last_run:
                last_run = True
            elif 2 >= n_length - len(g.graph.nodes) and last_run:
                break

            g.reset_all()

            if self._run_limit == run_num:
                break

            run_num += 1

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

