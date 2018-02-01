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
        reducers = cfg.reducers()

        for r in reducers:
            local_start = time.time()
            r.reduce(steiner)
            print str(r.__class__) + " in " + str(time.time() - local_start)

    if solve:
        solver = cfg.solver(steiner)
        solver.solve()

    return


for i in range(1, 100):
    filepath = "D:\steinertree\pace2017\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = filepath.format(i)
        print current_file
        start = time.time()
        process_file(current_file, False, True)
        print "Done in " + str(time.time() - start)
        print ""


