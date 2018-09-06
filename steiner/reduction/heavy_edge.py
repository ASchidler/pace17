from reduction.ntdk import NtdkReduction


class HeavyEdge:
    """ Checks if a terminal is guaranteed to be a leaf and adapts the incident edges weights if possible.
    Found in the source code of Krzysztof Maziarz and Adam Polak
    """

    def __init__(self):
        self._ran = False
        self._done = False
        self._adaptions = []

    def reduce(self, steiner, prev_cnt, curr_cnt):
        # Run only once
        if self._ran:
            return 0

        track = 0

        self._ran = True
        nbs = steiner.graph._adj

        for t in steiner.terminals:
            nb = nbs[t].items()

            if len(nb) < 2:
                continue

            c_w = None

            # Incident edges must have the same weight
            for (n, d) in nb:
                if c_w is None:
                    c_w = d['weight']

                if d['weight'] != c_w:
                    c_w = -1
                    break

            if c_w == -1:
                continue

            max_dist = max((NtdkReduction.modified_dijkstra(steiner, x, y, c_w, 40, False) for (x, tt1) in nb for
                           (y, tt2) in nb if y > x))

            # max_dist must be smaller then edges weight -> Leaf. If equal to cw-1 the weights would not change
            if max_dist >= c_w - 1:
                continue

            for (n, d) in nb:
                self._adaptions.append((t, n, c_w, max_dist + 1))
                steiner.graph[t][n]['weight'] = max_dist + 1

            track += 1

        return track

    def post_process(self, solution):
        changed = False
        w = solution[1]
        for (u, v, o, n) in self._adaptions:
            if solution[0].has_edge(u, v) and solution[0][u][v]['weight'] == n:
                solution[0][u][v]['weight'] = o
                w += o - n
                changed = True

        return (solution[0], w), changed
