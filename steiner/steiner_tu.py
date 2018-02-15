import sys
import config as cfg
import iparser as pp
import oparser as po
import signal


""" The real solver script that reads from stdin and outputs the solution """

steiner = pp.parse_pace_file(sys.stdin)
solver = cfg.solver(steiner)

# Reduce, in case of a timeout let the reduction finish in the background. One cannot kill a thread
reducers = cfg.reducers()
for r in reducers:
    r.reduce(steiner)

# Solve
solver.solve()

solution = solver.result
reducers.reverse()


for r in reducers:
    solution = r.post_process(solution)

po.parse_pace_output(solution)


