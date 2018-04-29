import steiner_graph as sg
import iparser as pp
import heapq as hq
from collections import defaultdict
import time
from bisect import insort
from sys import maxint
from heapq import heappush, heappop
import steiner_approximation as sa
import reduction.dual_ascent as da
import solver.heuristics.tsp_heuristic as tsp
import solver.heuristics.da_heuristic as dah
import solver.heuristics.mst_heuristic as mh
import solver.solver_bb as bb
import networkx as nx
import solver.solver_2k as kk
import d_heap as dh
import random
import solver.solver_pol as pol

import bounded_structures as bs

class DefaultingDict(dict):
    def __init__(self, dflt):
        super(DefaultingDict, self).__init__()
        self._dflt = dflt

    def __missing__(self, key):
        return self._dflt

def build_voronoi(steiner):
    queue = [(0, t, t) for t in steiner.terminals]
    max_node = max(n for n in steiner.graph.nodes) + 1
    voronoi_set = set()
    voronoi = {t: set() for t in steiner.terminals}
    closest = {n: [] for n in steiner.graph.nodes}
    lengths = {t: [maxint] * max_node for t in steiner.terminals}
    push = heappush
    pop = heappop
    nb = steiner.graph._adj
    done = set()

    while queue:
        dist, n, t = pop(queue)

        if (t, n) in done:
            continue
        done.add((t, n))

        if n not in voronoi_set:
            voronoi[t].add(n)
            voronoi_set.add(n)

        lengths[t][n] = dist
        closest[n].append((t, dist))

        for n2, dta in nb[n].items():
            tot = dist + dta['weight']
            if tot < lengths[t][n2]:
                lengths[t][n2] = tot
                push(queue, (tot, n2, t))

    return lengths

#[141, 149, 161, 163, 165, 167, 171, 173, 187, 193, 195]
file_path = "..\instances\lowTerm\instance187.gr"
#171
f = open(file_path, "r")
steiner1 = pp.parse_pace_file(f)
f.close()
f = open(file_path, "r")
steiner2 = pp.parse_pace_file(f)
f.close()
#
# nb = steiner1.graph._adj
# for t in steiner1.terminals:
#     m_c = min(d['weight'] for (_, d) in nb[t].items())
#     print "t {} vs {}".format(len([n for (n, d) in nb[t].items() if d['weight'] == m_c]), len(nb[t].items()))
#

# tm = time.time()
# result = build_voronoi(steiner2)
# print "All in one in {}".format(time.time() - tm)
#
# tm = time.time()
# steiner1.get_voronoi()
# [steiner1.get_closest(nn) for nn in steiner1.graph.nodes]
# print "Separate in {}".format(time.time() - tm)
#
#
# # Verify
# for (t, d) in ((t, steiner1.get_lengths(t)) for t in steiner1.terminals):
#     for (n, c) in d.items():
#         if result[t][n] != c:
#             print "Error {}".format(result[t][n] - c)
#

#print pol.solve(steiner1)

# ts = list(steiner1.terminals)
# target_ts = [ts[i] for i in xrange(0, 5)]
#
# set_size = 3
# max_terminals = (1 << 5) - 1
# set_pointers = [(1 << i) for i in xrange(0, set_size)]
# finished = False
#
# offset = 0
# length = 5
# v = reduce(lambda x, y: x | y, ((1 << i) for i in xrange(0, set_size)))
#
# full_subset = (1 << set_size) - 1
# subset = reduce(lambda x, y: x | y, ((1 << i) for i in xrange(0, set_size)))
# while subset <= max_terminals:
#     # Find mapping between enumeration and subsets
#     mapping = {}
#     cnt = 0
#     for i in xrange(0, length):
#         if (1 << i) & subset > 0:
#             mapping[cnt] = (1 << i)
#             cnt += 1
#
#     print "{0:05b}".format(subset)
#     # Find decompositions
#     # set_size - 1 since the subsets are symmetric
#     for i in range(1, 1 << (set_size - 1)):
#         s1 = reduce(lambda x, y: x | y, (mapping[j] for j in xrange(0, set_size) if ((1 << j) & i) > 0))
#         s2 = subset ^ s1
#         print "{0:b} {1:b}".format(s1, s2)
#
#     t = (subset | (subset - 1)) + 1
#     subset = t | ((((t & -t) / (subset & -subset)) >> 1) - 1)
#
ts = list(steiner1.terminals)
target_ts = [ts[i] for i in xrange(0, 5)]
tm = time.time()
results2 = [da.DualAscent.calc3(steiner1.graph, t, ts) for t in target_ts]
print "Result 2 in {}".format(time.time() - tm)

tm = time.time()
results1 = [da.DualAscent.calc2(steiner1.graph, t, ts) for t in target_ts]
print "Result 1 in {}".format(time.time() - tm)

print "Total gap (higher is better for the new) {}".format(sum(results2[i][0] - results1[i][0] for i in range(0, len(results1))))
max2, max1 = max(x for (x, _, _) in results2), max(x for (x, _, _) in results1)
print "Max gap (higher is better for the new) 2: {} 1: {} Diff: {}".format(max2, max1, max2 - max1)


print "Upper bound {}".format(steiner1.get_approximation().cost)
#
# # h = dah.DaHeuristic(steiner1)
# h2 = bh.BndHeuristic(steiner1)
# h3 = mh.MstHeuristic(steiner1)
# goal = len(steiner1.terminals) * 0.7
# tsl = list(steiner1.terminals)
# steiner1.get_closest(1)
# for i in range(1, 11):
#     ts = set()
#     for j in range(0, int(goal)):
#         ts.add(tsl[(j * 196613 + i) % len(tsl)])
#
#     tm = time.time()
#     results2 = h2.calculate(15, i, list(ts))
#     print "Result 2 {} in {}".format(results2, time.time() - tm)
#
#     tm = time.time()
#     results1 = h3.calculate(15, i, list(ts))
#     print "Result 1 {} in {}".format(results2, time.time() - tm)
#
#     tm = time.time()
#     results3 = h.calculate2(15, i, list(ts))
#     print "Result 3 {} in {}".format(results3, time.time() - tm)

# sbb = bb.SolverBb(steiner1)
# result = sbb.solve()
# print "Done {}".format(result.cost)

#nx.find_cliques(steiner1.graph)
#
# rands = [random.randint(0, 100) for i in xrange(0, 100000)]
# tm = time.time()
# q = ([], {}, 16)
#
# [dh.enqueue(q, rands[i], i) for i in xrange(0, 100000)]
# [dh.enqueue(q, random.randint(0, 10000), i) for i in xrange(0, 100000)]
# try:
#     while True:
#         dh.dequeue(q)
# except IndexError:
#     pass
# print "Result 2 in {}".format(time.time() - tm)
#
# qp = []
# tm = time.time()
# [heappush(qp, (rands[i], i)) for i in xrange(0, 100000)]
# [heappush(qp, (random.randint(0, 10000), i)) for i in xrange(0, 100000)]
# try:
#     while True:
#         heappop(qp)
# except IndexError:
#     pass
# print "Result 1 in {}".format(time.time() - tm)
#
# bq = bs.create_queue(100)
# [bs.enqueue(bq, rands[i], i) for i in xrange(0, 100000)]
# [bs.enqueue(bq, random.randint(0, 10000), i) for i in xrange(0, 100000)]
#
# try:
#     while True:
#         bs.dequeue(bq)
# except KeyError:
#     pass
# print "Result 3 in {}".format(time.time() - tm)