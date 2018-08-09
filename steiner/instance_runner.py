import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals
import steiner_graph as sg
import component_finder as cf
import sys
import reduction.dual_ascent as da
from reducer import DebugReducer

""" This runner runs all the public instances with debug oparser """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steiner = pp.parse_pace_file(f)
    solution = start_solve(steiner, solve, apply_reductions)

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


def start_solve(steiner, solve, apply_reductions):
    reducer = DebugReducer(cfg.reducers())

    if apply_reductions:
        reducer.reduce(steiner)

    if solve:
        #solution = solve_instance(steiner)
        solution = cf.decompose(steiner, lambda x: solve_instance(x), lambda x: start_solve(x, solve, apply_reductions))

        # This step is necessary as some removed edges and nodes have to be reintroduced in the solution
        if apply_reductions:
            solution = reducer.unreduce(solution[0], solution[1])

        return solution


def solve_instance(steiner):
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

    print "Solution found: " + str(solution[1])
    return solution


# Instances that are not solvable yet
hard_instances = [161, 162, 163, 164, 165, 171, 172, 173, 194, 195, 196, 200]
# Solvable but at the upper end of the timelimit
long_runtime = [150, 152, 167, 187, 189, 190, 192, 193, 197, 198, 199]
# All other instances are solvable in a feasible amount of time
easy_instances = [i for i in xrange(1, 200) if i not in hard_instances and i not in long_runtime]
lst = list(easy_instances)
lst.extend(long_runtime)

# 16x 0640/40896, almost no reductions
# 171 0243/01215, few reductions, unit weights
# 173 0243/01215, no reductions, most edges weight 1, some 2
# 195 0550/05000, no reductions, unit weights
# Not 160, 162 (u), 164(u), 190, 196
# Yes 2-160, 166, 168, 170, 174-188, 192,
# ? 200, 172, 194
# slow 198
#for i in [171]: # [171, 173, 195]:# (x for x in lst if x > 189): # hard_instances:
for i in long_runtime:
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"

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
