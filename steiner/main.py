import sys
import os.path
import steiner_graph as sg
import time
from solver import solver_2k as sv
from reduction import *
from preselection import *

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <file>"
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print "File does not exist"
    sys.exit()


def process_file(filename, solve, reduce):
    steiner = sg.SteinerGraph()
    steiner.parse_file(filename)

    if reduce:
        reducers = [incidence.IncidenceReduction(),
                    short_edges.ShortEdgeReduction(),
                    degree.DegreeReduction(),
                    component.ComponentReduction(),
                    terminal_distance.TerminalDistanceReduction(),
                    voronoi.VoronoiReduction(),
                    long_edges.LongEdgeReduction(),
                    ntdk.NtdkReduction(),
                    reachability.ReachabilityReduction(),
                    cut_reachability.CutReachabilityReduction(),
                    zeroedge.ZeroEdgeReduction()]

        for r in reducers:
            r.reduce(steiner)

    if solve:
        solver = sv.Solver2k(steiner)
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


