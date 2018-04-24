import config as cfg
from reducer import Reducer
from reduction.dual_ascent import DualAscent
from networkx import minimum_spanning_tree, is_connected
import steiner_graph as sg
import time


# TODO: Remove bound based reductions. Run dual ascent once at the end
class SolverBb:
    def __init__(self, steiner):
        self._upper_bound = steiner.get_approximation()
        self.steiner = steiner

    def solve(self):
        tm = time.time()
        print "Starting {} nodes, {} edges, {} terminals".format(len(self.steiner.graph.nodes), len(self.steiner.graph.edges),
                                                                len(self.steiner.terminals))
        approx = self.steiner.get_approximation()
        solution = self.start(self.steiner, (approx.tree, approx.cost))
        print "Solution found {} in {}".format(solution[0], time.time() - tm)
        return self._upper_bound

    # TODO: The bounding solution is not reduced. It is therefore with high probability always higher
    def start(self, steiner, c_bound):
        if not is_connected(steiner.graph):
            return None

        r = Reducer(cfg.reducers())

        r.reduce(steiner)

        print "Reduced {} nodes, {} edges, {} terminals".format(len(steiner.graph.nodes), len(steiner.graph.edges), len(steiner.terminals))
        if steiner.get_approximation().cost < c_bound[1]:
            approx = self.steiner.get_approximation()
            c_bound = (approx.tree, approx.cost)

        if steiner.lower_bound == c_bound[1]:
            solution = r.unreduce(steiner.get_approximation().tree, steiner.get_approximation().cost)
            print "Found solution"
            return solution
        elif steiner.lower_bound > c_bound[1]:
            print "Bound reached"
            return None

        # Find branching node
        max_dg = (0, None)
        is_spanning = True
        for (n, dg) in steiner.get_approximation().tree.degree:
            if n not in steiner.terminals and dg > max_dg[0]:
                if steiner.graph.has_node(n):
                    max_dg = (dg, n)
                else:
                    is_spanning = False

        # This may also happen if the approximation contains no node in the graph, check if mst...
        if max_dg[1] is None:
            if not is_spanning:
                mst = minimum_spanning_tree(steiner.graph)
                if any(x not in steiner.terminals for x in mst.nodes):
                    print "No nodes but not spanning..."

            # This should leave an MST...
            print "Cannot branch, found solution"
            return r.unreduce(c_bound[0], c_bound[1])

        print "Branching {} 0".format(max_dg[1])
        new_g = self.copy_graph(steiner)
        new_g.remove_node(max_dg[1])
        result = self.start(new_g, c_bound)

        if result is not None and result[1] < c_bound[1]:
            c_bound = result

        print "Branching {} 1".format(max_dg[1])
        new_g = self.copy_graph(steiner)
        new_g.terminals.add(max_dg[1])
        result = self.start(new_g, c_bound)
        if result is not None and result[1] < c_bound[1]:
            c_bound = result

        return r.unreduce(c_bound[0], c_bound[1])

    def copy_graph(self, g):
        new_g = sg.SteinerGraph()
        new_g.terminals = set(g.terminals)
        for (u, v, d) in g.graph.edges(data='weight'):
            new_g.add_edge(u, v, d)

        return new_g
