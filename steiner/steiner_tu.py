import sys
import config as cfg
import iparser as pp
import oparser as po
import reduction.degree as dg
import component_finder as cf
import signal


""" The real solver script that reads from stdin and outputs the solution """

steinerx = pp.parse_pace_file(sys.stdin)
dr = dg.DegreeReduction()
dr.reduce(steinerx, 0, False)
finder = cf.ComponentFinder()

components = finder.decompose([steinerx])

results = []

for steiner in components:
    reducers = cfg.reducers()
    contractors = cfg.contractors()
    last_run = False

    while True:
        cnt = 0
        for r in reducers:
            cnt = cnt + r.reduce(steiner, cnt, last_run)

        steiner._lengths = {}
        steiner._approximation = None

        for c in contractors:
            cnt = cnt + c.reduce(steiner, cnt, last_run)

        steiner._lengths = {}
        steiner._approximation = None
        steiner._restricted_lengths = {}
        steiner._restricted_closest = None
        steiner._radius = None
        steiner._voronoi_areas = None

        if cnt == 0:
            if last_run:
                break
            last_run = True
        else:
            last_run = False

    # Solve
    # Distance matrix may be incorrect due to preprocessing, restore
    steiner._lengths = {}
    steiner._approximation = None
    solver = cfg.solver(steiner)

    solver.solve()
    solution = solver.result

    reducers.reverse()

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

final_result = finder.build_solutions(results)
change = True
while change:
    ret = dr.post_process(final_result)
    final_result = ret[0]
    change = ret[1]

po.parse_pace_output(final_result)


