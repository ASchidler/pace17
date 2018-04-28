import sys
import config as cfg
import iparser as pp
import oparser as po
import reduction.degree as dg
import component_finder as cf
from reducer import Reducer

""" The real solver script that reads from stdin and outputs the solution """

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
