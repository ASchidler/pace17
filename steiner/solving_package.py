from networkx import is_connected, nodes
import component_finder as cf
import oparser.debug as o_dbg
import oparser.pace as o_pace
import reducer as red
import config as cfg
import time

from structures.steiner_graph import SteinerGraph

"""Packages the whole solver so it can be called from different runners"""


def run(steiner, debug=False, solve=True, reductions=True, verify=False, split=False, pace_only=False, prnt=True):
    """Calls the necessary functions"""

    # Copy graph for verification
    steiner_cp = None
    start_time = None

    if verify:
        steiner_cp = SteinerGraph()
        steiner_cp.graph = steiner.graph.copy()
        steiner_cp.terminals = set(steiner.terminals)

    if debug:
        print "Loaded instance with {} vertices, {} edges, {} terminals".format(len(steiner.graph.nodes),
                                                                                len(steiner.graph.edges),
                                                                                len(steiner.terminals))
        start_time = time.time()

    solution = _start_solve(steiner, debug, solve, reductions, split, pace_only)

    # Output solution
    if not verify or _verify(steiner_cp, solution):
        if prnt:
            if debug:
                o_dbg.parse(solution)
            else:
                o_pace.parse(solution)

    if debug:
        print "Completed in {}".format(time.time() - start_time)

    return solution


def _start_solve(steiner, debug, solve, apply_reductions, split, pace_only):
    """Reduces the whole graph and splits the solving if necessary"""
    reducer = red.DebugReducer(cfg.reducers(pace_only)) if debug else red.Reducer(cfg.reducers(pace_only))

    if apply_reductions:
        reducer.reduce(steiner)

    if solve:
        if split:
            solution = cf.decompose(steiner, lambda x: _solve_instance(x, debug, split),
                                    lambda x: _start_solve(x, debug, solve, apply_reductions, split, pace_only),
                                    debug)
        else:
            solution = _solve_instance(steiner, debug, split)

        # This step is necessary as some removed edges and nodes have to be reintroduced in the solution
        if apply_reductions:
            solution = reducer.unreduce(solution[0], solution[1])

        return solution


def _solve_instance(steiner, debug, split):
    if debug:
        print "Solving instance with {} vertices, {} edges, {} terminals".format(len(steiner.graph.nodes),
                                                                                 len(steiner.graph.edges),
                                                                                 len(steiner.terminals))

    # Reset lengths as they may not reflect reality after the reductions
    steiner._lengths = {}

    # Solve
    solver = cfg.solver(steiner)
    solution = solver.solve()

    # Quick validity checks
    if debug and split:
        if not is_connected(solution[0]):
            print "*** Unconnected solution"

        for n in steiner.terminals:
            if n not in nodes(solution[0]):
                print "*** Missing a terminal"

        print "Solution found: " + str(solution[1])

    return solution


def _verify(steiner, solution):
    total_sum = 0
    correct = True

    if not is_connected(solution[0]):
        print "*** Disconnected solution after unreduce"
        correct = False

    for (u, v, d) in solution[0].edges(data='weight'):
        total_sum = total_sum + d
        if not steiner.graph.has_edge(u, v) or steiner.graph[u][v]['weight'] != d:
            print "*** Unknown edge {}-{} in solution after unreduce".format(u, v)
            correct = False

    if total_sum != solution[1]:
        print "*** Total sum {} does not match expected {} after unreduce".format(total_sum, solution[1])
        correct = False

    for t in steiner.terminals:
        if not solution[0].has_node(t):
            print "*** Missing terminal {} in solution after unreduce".format(t)
            correct = False

    return correct
