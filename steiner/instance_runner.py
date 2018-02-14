import time

import networkx as nx
import steiner.parser.pace_parser as pp

import config as cfg

""" This runner runs all the public instances with debug output """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose output"""

    f = open(filename, "r")
    steiner = pp.parse_file(f)
    reducers = cfg.reducers()

    if apply_reductions:
        cnt_edge = len(nx.edges(steiner.graph))
        cnt_nodes = len(nx.nodes(steiner.graph))

        for r in reducers:
            local_start = time.time()
            reduced = r.reduce(steiner)
            print "Reduced {} needing {} in {}"\
                .format(reduced, str(time.time() - local_start), str(r.__class__))

        print "{} nodes and {} edges removed "\
            .format(cnt_nodes - len(nx.nodes(steiner.graph)), cnt_edge - len(nx.edges(steiner.graph)))

    if solve:
        solver = cfg.solver(steiner)
        solution = solver.solve()

        # Quick validity checks
        if not nx.is_connected(solution[0]):
            print "*** Unconnected solution"

        for n in steiner.terminals:
            if n not in nx.nodes(solution[0]):
                print "*** Missing a terminal"

    # This step is necessary as some removed edges and nodes have to be reintroduced in the solution
    if apply_reductions and solve:
        reducers.reverse()
        solution = solver.result

        for r in reducers:
            solution = r.post_process(solution)

    if solve:
        print "Solution found: " + str(solution[1])


# Exceptionally slow instances: 101, 123, 125 (125 is currently the maximum)
for i in range(125, 200):
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = file_path.format(i)
        print current_file
        start = time.time()
        process_file(current_file, True, True)
        print "Done in " + str(time.time() - start)
        print ""
