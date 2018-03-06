import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals
import solver.label_store as ls
import steiner_graph as sg
import component_finder as cf

""" This runner runs all the public instances with debug oparser """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steinerx = pp.parse_pace_file(f)

    c_finder = cf.ComponentFinder()
    # Count mismatches the real count to kickstart the loop
    component_cnt = 0
    components = [steinerx]
    results = []

    while component_cnt != len(components):
        component_cnt = len(components)
        components = c_finder.decompose(components)

        for steiner in components:
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
                        print "Reduced {} needing {} in {}" \
                            .format(reduced, str(time.time() - local_start), str(r.__class__))
                    if cnt_changes == 0:
                        break

                print "{} nodes, {} edges and {} terminals removed " \
                    .format(cnt_nodes - len(nx.nodes(steiner.graph)), cnt_edge - len(nx.edges(steiner.graph)),
                            cnt_terminals - len(steiner.terminals))

        # No use to retry decomposing if no reductions are performed
        if not apply_reductions:
            break

    if solve:
        for steiner in components:
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
            if apply_reductions:
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

            results.append(solution)
            print "Solution found: " + str(solution[1])

    total_solution = c_finder.build_solutions(results)

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


# Exceptionally slow instances: 101, 123, 125 (125 is currently the maximum)
for i in range(125, 200):
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = file_path.format(i)
        print current_file
        start = time.time()
        e1 = process_file(current_file, True, True)
        #e2 = process_file(current_file, True, True)
        #if e1 != e2:
        #    print "*************** Difference in instance "+ str(i)
        print "Done in " + str(time.time() - start)
        print ""