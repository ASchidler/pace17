import time
import os
import config as cfg
import steiner.parser.pace_parser as pp
import thread
import threading as th

terminal_limit = 50
time_limit = 120

filepath = "..\\testInstances\\"
optimums = {}

optimum_file = open(filepath + "optimums.csv", "r")
for line in optimum_file:
    fields = line.strip(' \xa0\n').split(";")
    optimums[fields[0].strip()] = int(fields[1])

for filename in os.listdir(filepath):
    if filename.endswith(".stp"):
        instance_name = filename.split(".")[0]
        start = time.time()
        steiner = pp.parse_file(filepath + filename)

        if len(steiner.terminals) > terminal_limit:
            print "{}: Too many terminals {}".format(instance_name, len(steiner.terminals))
            continue

        # Used to watch running time
        thread_start = time.time()

        # Reduce, in case of a timeout let the reduction finish in the background. One cannot kill a thread
        reducers = cfg.reducers()
        for r in reducers:
            if (time.time() - thread_start) <= time_limit:
                thr = th.Thread(target=r.reduce, args=(steiner,))
                thr.start()
                while thr.is_alive() and (time.time() - thread_start) <= time_limit:
                    time.sleep(0.1)

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

        for r in reducers:
            solution = r.post_process(solution)

        if instance_name not in optimums:
            print "*** {}: Unknown instance".format(instance_name)
        elif solution[1] == optimums[instance_name]:
            print "{}: Completed in {}".format(instance_name, str(time.time() - start))
        else:
            print "*** {}: Wrong result, expected {} actual {}"\
                .format(instance_name, optimums[instance_name], solution[1])
