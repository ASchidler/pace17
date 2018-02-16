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

while True:
    cnt = 0
    for r in reducers:
        cnt = cnt + r.reduce(steiner)

    if cnt == 0:
        break

# Solve
solver.solve()

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

po.parse_pace_output(solution)


