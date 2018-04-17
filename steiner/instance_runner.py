import time

import networkx as nx
import iparser as pp

import config as cfg
import reduction.terminals as terminals
import solver.label_store as ls
import steiner_graph as sg
import component_finder as cf
import sys
import reduction.dual_ascent as da

""" This runner runs all the public instances with debug oparser """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steinerx = pp.parse_pace_file(f)
    c_finder = cf.ComponentFinder()

    components = [steinerx]
    results = []

    #components = c_finder.decompose(components)
    print "Split into {} components".format(len(components))
    for c in components:
        print "{} nodes".format(len(nx.nodes(c.graph)))

    for steiner in components:
        reducers = cfg.reducers()
        contractors = cfg.contractors()

        if apply_reductions:
            cnt_edge = len(nx.edges(steiner.graph))
            cnt_nodes = len(nx.nodes(steiner.graph))
            cnt_terminals = len(steiner.terminals)
            last_run = False

            while True:
                cnt_changes = 0

                for r in reducers:
                    if len(nx.nodes(steiner.graph)) > 1:
                        local_start = time.time()
                        reduced = r.reduce(steiner, cnt_changes, last_run)
                        cnt_changes = cnt_changes + reduced
                        print "Reduced {} needing {} in {}" \
                            .format(reduced, str(time.time() - local_start), str(r.__class__))

                steiner.reset_all()

                for c in contractors:
                    if len(nx.nodes(steiner.graph)) > 1:
                        local_start = time.time()
                        reduced = c.reduce(steiner, cnt_changes, last_run)
                        cnt_changes = cnt_changes + reduced
                        print "Contracted {} needing {} in {}" \
                            .format(reduced, str(time.time() - local_start), str(c.__class__))

                if cnt_changes == 0:
                    if last_run:
                        break
                    last_run = True
                else:
                    last_run = False

            print "{} nodes, {} edges and {} terminals removed " \
                .format(cnt_nodes - len(nx.nodes(steiner.graph)), cnt_edge - len(nx.edges(steiner.graph)),
                        cnt_terminals - len(steiner.terminals))

        if solve:
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
                    for c in contractors:
                        ret = c.post_process(solution)
                        solution = ret[0]
                        change = change or ret[1]
                    if not change:
                        break

            results.append(solution)
            print "Solution found: " + str(solution[1])

        print "\n\n"

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


# Instances that are not solvable yet
hard_instances = [131, 141, 149, 153, 161, 163, 165, 167, 169, 171, 173, 175, 177, 187, 193, 195, 197, 199]
# Instances that are stuck (either forever or too long) in reduction mode
long_reduction = [113, 129, 151, 181, 189]
# All other instances are solvable in a feasible amount of time
easy_instances = [i for i in xrange(1, 200) if i not in hard_instances and i not in long_reduction]

for i in [197]:
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
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