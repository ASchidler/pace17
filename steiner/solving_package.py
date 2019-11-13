from networkx import is_connected, nodes
import component_finder as cf
import oparser.debug as o_dbg
import oparser.pace as o_pace
import reducer as red
import config as cfg
import time
from solver.solver_2k import Solver2kConfig

from structures.steiner_graph import SteinerGraph

"""Packages the whole solver so it can be called from different runners"""


class SolvingConfig:
    def __init__(self, debug=False, solve=True, apply_reductions=True, verify=False, split=False, pace_only=False,
                 print_output=False, heavy_edges=False, heap_width=16, bucket_limit=5000, use_da=True, use_store=True,
                 use_root=True, node_limit=2000, node_ratio_limit=3, reduction_limit=0):
        self.debug = debug
        self.solve = solve
        self.apply_reductions = apply_reductions
        self.verify = verify
        self.split = split
        self.pace_only = pace_only
        self.print_output = print_output
        self.heavy_edges = heavy_edges
        self.heap_width = heap_width
        self.use_da = use_da
        self.use_store = use_store
        self.use_root = use_root
        self.bucket_limit = bucket_limit
        self.node_limit = node_limit
        self.node_ratio_limit = node_ratio_limit
        self.reduction_limit = reduction_limit


def run(steiner, config):
    """Calls the necessary functions"""

    # Copy graph for verification
    steiner_cp = None
    start_time = None

    if config.verify:
        steiner_cp = SteinerGraph()
        steiner_cp.graph = steiner.graph.copy()
        steiner_cp.terminals = set(steiner.terminals)

    if config.debug:
        print "Loaded instance with {} vertices, {} edges, {} terminals".format(len(steiner.graph.nodes),
                                                                                len(steiner.graph.edges),
                                                                                len(steiner.terminals))
        start_time = time.time()

    #from networkx.algorithms.planarity import check_planarity
    #plan = check_planarity(steiner.graph)
    #if plan:
    #    print "Graph is planar"
    solution = _start_solve(steiner, config)

    # Output solution
    if not config.verify or _verify(steiner_cp, solution):
        if config.print_output:
            if config.debug:
                o_dbg.parse(solution)
            else:
                o_pace.parse(solution)

    if config.debug:
        print "Completed in {}".format(time.time() - start_time)

    return solution


def _start_solve(steiner, config):
    """Reduces the whole graph and splits the solving if necessary"""
    reducer = red.DebugReducer(cfg.reducers(config.pace_only, config.heavy_edges), reduction_limit=config.reduction_limit)\
        if config.debug else red.Reducer(cfg.reducers(config.pace_only, config.heavy_edges), reduction_limit=config.reduction_limit)

    if config.apply_reductions:
        reducer.reduce(steiner)

    # Write reduced graph for debug reasons
    # f = open("output.stp", "w+")
    # f.write("SECTION Graph\n")
    # f.write("Nodes {}\n".format(len(steiner.graph.nodes)))
    # f.write("Edges {}\n".format(len(steiner.graph.edges)))
    # for u, v in steiner.graph.edges:
    #     f.write("E {} {} {}\n".format(u, v, steiner.graph[u][v]['weight']))
    #
    # f.write("END\n\nSECTION Terminals\n")
    # f.write("Terminals {}\n".format(len(steiner.terminals)))
    # for t in steiner.terminals:
    #     f.write("T {}\n".format(t))
    # f.write("END\n\nEOF\n")
    # f.close()
    # end write reduced graph

    if config.solve:
        solution = cf.decompose(steiner, lambda x: _solve_instance(x, config),
                                lambda x: _start_solve(x, config),
                                config.debug, config.split)

        # This step is necessary as some removed edges and nodes have to be reintroduced in the solution
        if config.apply_reductions:
            solution = reducer.unreduce(solution[0], solution[1])

        return solution


def _solve_instance(steiner, config):
    if config.debug:
        print "Solving instance with {} vertices, {} edges, {} terminals".format(len(steiner.graph.nodes),
                                                                                 len(steiner.graph.edges),
                                                                                 len(steiner.terminals))

    # Reset lengths as they may not reflect reality after the reductions
    steiner._lengths = {}

    # Solve
    solver = cfg.solver(steiner, Solver2kConfig(config.heap_width, config.bucket_limit, config.use_root,
                                                config.use_store, config.use_da),
                        config.node_limit, config.node_ratio_limit)
    solution = solver.solve()

    # Quick validity checks
    if config.debug and config.split:
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
