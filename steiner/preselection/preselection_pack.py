from sys import maxint

import nearest_vertex as nv
import reduction.degree as dg
import short_links as sl


class NvSlPack:
    """Combines terminal contractions, nearest vertex and short links reduction and reiterates reduction until
    failure"""

    def __init__(self, threshold=0.01):
        self._sl = sl.ShortLinkPreselection()
        self._nv = nv.NearestVertex()
        self._dg = dg.DegreeReduction()
        self._threshold = threshold
        self._counter = maxint / 2

    def reduce(self, steiner, prev_cnt, curr_cnt):
        self._counter += prev_cnt
        if self._counter < self._threshold * len(steiner.graph.edges):
            return 0
        else:
            self._counter = 0

        total = 0
        this_run = -1
        while this_run != 0:
            this_run = 0
            this_run += self._nv.reduce(steiner, prev_cnt, curr_cnt)
            this_run += self._sl.reduce(steiner, prev_cnt, curr_cnt)

            if this_run > 0:
                this_run += self._dg.reduce(steiner, prev_cnt, curr_cnt)

            total += this_run

        if total > 0:
            steiner._voronoi_areas = None
            steiner._lengths = {}
            steiner._closest_terminals = None

        return total

    def post_process(self, solution):
        result1 = self._nv.post_process(solution)
        result2 = self._sl.post_process(result1[0])
        result3 = self._dg.post_process(result2[0])

        return result3[0], result1[1] or result2[1] or result3[1]
