import sys
import config as cfg
import iparser as pp
import oparser as po
from reducer import Reducer

""" This script is used for PACE. It reads the instance from STDIN and has no extra output except the solution"""

steiner = pp.parse_pace_file(sys.stdin)

reducer = Reducer(cfg.reducers())
reducer.reduce(steiner)

# Solve
# Distance matrix may be incorrect due to preprocessing, restore
steiner._lengths = {}
solver = cfg.solver(steiner)

solution = solver.solve()

final_result = reducer.unreduce(solution[0], solution[1])
po.parse_pace_output(final_result)
