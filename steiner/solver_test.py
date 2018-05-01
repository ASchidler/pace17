import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals
import steiner_graph as sg
import component_finder as cf
import reduction.degree as dg
import sys
import solver.solver_bc as bc

""" This runner runs all the public instances with debug oparser """


def process_file(filename):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steinerx = pp.parse_pace_file(f)
    solver = bc.SolverBc(steinerx, steinerx.terminals, None)
    solution = solver.solve()


# Exceptionally slow instances: 101, 123, 125 (125 is currently the maximum)
for i in range(1, 2):
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        sys.setcheckinterval(1000)
        current_file = file_path.format(i)
        print current_file
        start = time.time()
        e1 = process_file(current_file)
        print "Done in " + str(time.time() - start)
        print ""