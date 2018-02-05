import sys
import os.path
import steiner_graph as sg
import time
import graph_costs
import config as cfg

import networkx as nx

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <file>"
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print "File does not exist"
    sys.exit()


def process_file(filename, solve, apply_reductions):
    steiner = sg.SteinerGraph()
    steiner.parse_file(filename)

    if apply_reductions:
        cnt_edge = len(nx.edges(steiner.graph))
        cnt_nodes = len(nx.nodes(steiner.graph))
        reducers = cfg.reducers()

        for r in reducers:
            local_start = time.time()
            reduced = r.reduce(steiner)
            print "Reduced {} needing {} in {}".format(reduced, str(time.time() - local_start), str(r.__class__))

        print "{} nodes and {} edges removed ".format(cnt_nodes - len(nx.nodes(steiner.graph)), cnt_edge - len(nx.edges(steiner.graph)))

    if solve:
        solver = cfg.solver(steiner)
        solution = solver.solve()
        if not nx.is_connected(solution[0]):
            print "*** Unconnected solution"

        for n in steiner.terminals:
            if n not in nx.nodes(solution[0]):
                print "***Missing a terminal"

    if apply_reductions and solve:
        reducers.reverse()

        for r in reducers:
            solution = r.post_process(solution)

    if solve:
        print "Solution found: " + str(solution[1])

    return


for i in range(1, 200):
    filepath = "D:\steinertree\pace2017\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = filepath.format(i)
        print current_file
        start = time.time()
        process_file(current_file, True, True)
        print "Done in " + str(time.time() - start)
        print ""


