import time
import os
import config as cfg
import steiner.parser.pace_parser as pp
import thread

terminal_limit = 50
time_limit = 60

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

        reducers = cfg.reducers()

        for r in reducers:
            r.reduce(steiner)

        solver = cfg.solver(steiner)

        if len(steiner.terminals) > terminal_limit:
            print "{}: Too many terminals {}".format(instance_name, len(steiner.terminals))
            continue

        thread_start = time.time()
        thread.start_new_thread(solver.solve, ())

        failed = False
        while solver.result is None:
            time.sleep(1)
            if (time.time() - thread_start) > time_limit:
                solver.stop = True
                print "{}: Timeout".format(instance_name)
                failed = True
                break

        if not failed:
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
