import time
import os
import config as cfg
import iparser as pp
import thread
import threading as th
import steiner_graph as st
import networkx as nx
import reduction.terminals as terminals

terminal_limit = 50
time_limit = 120

file_path = "..\\testInstances\\"
optimums = {}

optimum_file = open(file_path + "optimums.csv", "r")
for line in optimum_file:
    fields = line.strip(' \xa0\n').split(";")
    optimums[fields[0].strip()] = int(fields[1])

for filename in os.listdir(file_path):
    if filename.endswith(".stp"):
        instance_name = filename.split(".")[0]
        start = time.time()
        f = open(file_path + filename, "r")
        steiner = pp.pace.parse_file(f)

        if len(steiner.terminals) > terminal_limit:
            print "{}: Too many terminals {}".format(instance_name, len(steiner.terminals))
            continue

        # Used to watch running time
        thread_start = time.time()

        # Reduce, in case of a timeout let the reduction finish in the background. One cannot kill a thread
        reducers = cfg.reducers()
        while True:
            cnt = len(nx.nodes(steiner.graph)) + len(nx.edges(steiner.graph))
            for r in reducers:
                if (time.time() - thread_start) <= time_limit:
                    thr = th.Thread(target=r.reduce, args=(steiner,))
                    thr.start()
                    while thr.is_alive() and (time.time() - thread_start) <= time_limit:
                        time.sleep(0.1)

                if len(list(nx.connected_components(steiner.graph))) > 1:
                    pass

                for t in steiner.terminals:
                    for (k, v) in steiner.get_voronoi().items():
                        if t in v:
                            pass
                    if t not in nx.nodes(steiner.graph):
                        pass

            cnt2 = len(nx.nodes(steiner.graph)) + len(nx.edges(steiner.graph))

            if cnt == cnt2:
                break
            cnt = cnt2
        steiner._lengths = {}
        steiner._approximation = None
        # Wait for solving to complete
        solver = cfg.solver(steiner)
        thread.start_new_thread(solver.solve, ())
        while solver.result is None and (time.time() - thread_start) <= time_limit:
            time.sleep(1)

        # Check for a result
        if solver.result is None:
            solver.stop = True
            print "{}: Timeout".format(instance_name)
            continue

        solution = solver.result
        reducers.reverse()

        while True:
            change = False
            for r in reducers:
                ret = r.post_process(solution)
                solution = ret[0]
                change = change or ret[1]

            if not change:
                break

        if instance_name not in optimums:
            print "*** {}: Unknown instance".format(instance_name)
        elif solution[1] == optimums[instance_name]:
            print "{}: Completed in {}".format(instance_name, str(time.time() - start))
        else:
            print "*** {}: Wrong result, expected {} actual {}"\
                .format(instance_name, optimums[instance_name], solution[1])
