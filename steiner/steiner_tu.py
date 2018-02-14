import sys
import config as cfg
import iparser as pp
import oparser as po
import signal


""" The real solver script that reads from stdin and outputs the solution """


stop = False
steiner = pp.parse_pace_file(sys.stdin)
solver = cfg.solver(steiner)


def stop_execution(a, b):
    global stop, solver
    stop = True
    solver.stop = True


signal.signal(signal.SIGINT, stop_execution)
signal.signal(signal.SIGTERM, stop_execution)

# Reduce, in case of a timeout let the reduction finish in the background. One cannot kill a thread
reducers = cfg.reducers()
for r in reducers:
    if not stop:
        r.reduce(steiner)

# Solve
solver.solve()

solution = solver.result
reducers.reverse()

if stop:
    exit(1)

for r in reducers:
    solution = r.post_process(solution)

po.parse_pace_output(solution)


