import sys
import config as cfg
import iparser as pp
import oparser as po
import reduction.degree as dg
import component_finder as cf
from reducer import Reducer

""" The real solver script that reads from stdin and outputs the solution """

steinerx = pp.parse_pace_file(sys.stdin)
dr = dg.DegreeReduction()
dr.reduce(steinerx, 0, False)
finder = cf.ComponentFinder()

components = finder.decompose([steinerx])

results = []

for steiner in components:
    reducer = Reducer(cfg.reducers())

    # Solve
    # Distance matrix may be incorrect due to preprocessing, restore
    steiner._lengths = {}
    solver = cfg.solver(steiner)

    solver.solve()
    solution = solver.result

    results.append(reducer.unreduce(solution[0], solution[1]))

final_result = finder.build_solutions(results)
change = True
while change:
    ret = dr.post_process(final_result)
    final_result = ret[0]
    change = ret[1]

po.parse_pace_output(final_result)


