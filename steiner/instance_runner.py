import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals
import solver.label_store as ls
import steiner_graph as sg
import component_finder as cf
import sys
import reduction.dual_ascent as da
from reducer import DebugReducer

""" This runner runs all the public instances with debug oparser """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steinerx = pp.parse_pace_file(f)
    c_finder = cf.ComponentFinder()

    components = [steinerx]
    results = []

    #components = c_finder.decompose(components)
    print "Split into {} components".format(len(components))
    for c in components:
        print "{} nodes".format(len(nx.nodes(c.graph)))

    for steiner in components:
        reducer = DebugReducer(cfg.reducers())

        if apply_reductions:
            reducer.reduce(steiner)

        if solve:
            steiner._lengths = {}
            # Reset lengths as they may not reflect reality after the reductions
            solver = cfg.solver(steiner)
            solution = solver.solve()

            # Quick validity checks
            if not nx.is_connected(solution[0]):
                print "*** Unconnected solution"

            for n in steiner.terminals:
                if n not in nx.nodes(solution[0]):
                    print "*** Missing a terminal"

            # This step is necessary as some removed edges and nodes have to be reintroduced in the solution
            if apply_reductions:
                solution = reducer.unreduce(solution[0], solution[1])

            results.append(solution)
            print "Solution found: " + str(solution[1])

        print "\n\n"

    if solve:
        # total_solution = c_finder.build_solutions(results)
        total_solution = solution
        # Verify
        f = open(filename, "r")
        steiner2 = pp.parse_pace_file(f)
        total_sum = 0

        if not nx.is_connected(total_solution[0]):
            print "*** Disconnected solution after unreduce"

        for (u, v, d) in total_solution[0].edges(data='weight'):
            total_sum = total_sum + d
            if not steiner2.graph.has_edge(u, v) or steiner2.graph[u][v]['weight'] != d:
                print "*** Unknown edge {}-{} in solution after unreduce".format(u, v)

        if total_sum != total_solution[1]:
            print "*** Total sum {} does not match expected {} after unreduce".format(total_sum, total_solution[1])

        for t in steiner2.terminals:
            if not total_solution[0].has_node(t):
                print "*** Missing terminal {} in solution after unreduce".format(t)

        print "Final solution: {}".format(total_solution[1])
        return total_solution[1]


# Instances that are not solvable yet
hard_instances = [161, 163, 165, 171, 173, 187, 193, 195]
# All other instances are solvable in a feasible amount of time
easy_instances = [i for i in xrange(1, 200) if i not in hard_instances]
long_runtime = [167, 197, 199]
solved_but_not_optil = [169, 197, 199]
lst = list(set(easy_instances))
# lst.extend(reversed(hard_instances))

# Error 131 with mst heuristic
# 173 small in no reductions, 187 large almost no reductions
# 171 small, few nodes reduced,
# 167 hard to crack reasonable reduction
# 167, 171, 173, ?193
for i in [197]:# (x for x in lst if x > 189): # hard_instances:
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        sys.setcheckinterval(1000)
        current_file = file_path.format(i)
        print current_file
        start = time.time()
        e1 = process_file(current_file, True, True)
        # e2 = process_file(current_file, True, False)
        # if e1 != e2:
        #     print "*************** Difference in instance "+ str(i)
        print "Done in " + str(time.time() - start)
        print ""
