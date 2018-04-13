import short_links as sl
import nearest_vertex as nv
import reduction.degree as dg
import reduction.terminals as t


class NvSlPack:
    def __init__(self):
        self._sl = sl.ShortLinkPreselection()
        self._nv = nv.NearestVertex()
        self._dg = dg.DegreeReduction()
        self._t = t.TerminalReduction()

    def reduce(self, steiner, cnt, last_run):
        total = 0
        this_run = -1
        while this_run != 0:
            this_run = 0
            this_run += self._nv.reduce(steiner, cnt, last_run)
            this_run += self._sl.reduce(steiner, cnt, last_run)

            if this_run > 0:
                this_run += self._dg.reduce(steiner, cnt, last_run)
                this_run += self._t.reduce(steiner, cnt, last_run)

            total += this_run

        return total

    def post_process(self, solution):
        result1 = self._nv.post_process(solution)
        result2 = self._sl.post_process(result1[0])
        result3 = self._dg.post_process(result2[0])
        result4 = self._t.post_process(result3[0])

        return result4[0], result1[1] or result2[1] or result3[1] or result4[1]