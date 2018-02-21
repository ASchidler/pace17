import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals

""" This runner runs all the public instances with debug oparser """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steiner = pp.parse_pace_file(f)
    reducers = cfg.reducers()

    if apply_reductions:
        cnt_edge = len(nx.edges(steiner.graph))
        cnt_nodes = len(nx.nodes(steiner.graph))
        cnt_terminals = len(steiner.terminals)

        while True:
            cnt_changes = 0
            for r in reducers:
                local_start = time.time()
                reduced = r.reduce(steiner)
                cnt_changes = cnt_changes + reduced
                print "Reduced {} needing {} in {}"\
                    .format(reduced, str(time.time() - local_start), str(r.__class__))
            if cnt_changes == 0:
                break

        print "{} nodes, {} edges and {} terminals removed "\
            .format(cnt_nodes - len(nx.nodes(steiner.graph)), cnt_edge - len(nx.edges(steiner.graph)),
                    cnt_terminals - len(steiner.terminals))

    if solve:
        steiner._lengths = {}
        steiner._approximation = None
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
    if apply_reductions and solve:
        reducers.reverse()
        solution = solver.result

        while True:
            change = False
            for r in reducers:
                ret = r.post_process(solution)
                solution = ret[0]
                change = change or ret[1]
            if not change:
                break

        # Verify
        f = open(filename, "r")
        steiner2 = pp.parse_pace_file(f)
        total_sum = 0
        if not nx.is_connected(solution[0]):
            print "*** Disconnected solution after unreduce"

        for (u, v, d) in solution[0].edges(data='weight'):
            total_sum = total_sum + d
            if not steiner2.graph.has_edge(u, v) or steiner2.graph[u][v]['weight'] != d:
                print "*** Unknown edge {}-{} in solution after unreduce".format(u, v)

        if total_sum != solution[1]:
            print "*** Total sum does not match after unreduce"

        for t in steiner2.terminals:
            if not solution[0].has_node(t):
                print "*** Missing terminal {} in solution after unreduce".format(t)

    if solve:
        print "Solution found: " + str(solution[1])
        return solution[1]


# Exceptionally slow instances: 101, 123, 125 (125 is currently the maximum)
for i in range(1, 200):
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = file_path.format(i)
        print current_file
        start = time.time()
        #e1 = process_file(current_file, True, False)
        e2 = process_file(current_file, True, True)
        # if e1 != e2:
        #     print "*************** Difference in instance "+ str(i)
        print "Done in " + str(time.time() - start)
        print ""
