from time import time


class DebugReduction:
    """Enhances the reduced with debug statements"""
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
    """Employs reductions until no more reductions can be performed. Can also reverse them for solutions"""

    def __init__(self, reducers, run_limit=0):
        self._reducers = reducers
        self._run_limit = run_limit

    def reduce(self, g):
        run_num = 1
        prev_changes = len(g.graph.edges)

        while True:
            cnt_changes = 0

            for r in self._reducers:
                if len(g.graph.nodes) > 1:
                    reduced = r.reduce(g, prev_changes, cnt_changes)
                    cnt_changes = cnt_changes + reduced
                else:
                    return

            g.reset_all()

            if cnt_changes == 0 or run_num == self._run_limit:
                break

            prev_changes = cnt_changes
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
    def __init__(self, reducers, run_limit=0):
        new_reducers = [DebugReduction(r) for r in reducers]
        Reducer.__init__(self, new_reducers, run_limit)

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

