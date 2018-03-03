import solver.solver_2k as sv


class SmtHeuristic:
    """A heuristic that uses steiner maximum trees of smaller terminal subets as a lower bound """
    def __init__(self, steiner, limit):
        self.steiner = steiner
        self.limit = limit
        self.results = {}

    def calculate(self, n, set_id, ts):
        # Last node is the root node
        root_node = ts[len(ts)-1]

        # Copy list to not change the input list
        ts2 = list(ts)
        # For this heuristic treat the current node as as terminal
        ts2.append(n)
        # Root node as appended anyway, so remove as a choice
        ts2.remove(root_node)

        max_val = 0
        # Find all subsets with size within the limit
        for i in range(1, 1 << len(ts2)):
            # Subset must contain at least to elements. Determine by counting the 1s in the binary representation
            if 2 <= bin(i).count("1") <= self.limit:
                if i in self.results:
                    val = self.results[i]
                else:
                    # Translate ID to set
                    active_set = []
                    for j in range(0, len(ts2)):
                        if (i & (1 << j)) > 0:
                            active_set.append(ts2[j])

                    # Root node is always included
                    active_set.append(root_node)
                    # Solve this problem without heuristics
                    slv = sv.Solver2k(self.steiner, active_set, [])
                    val = slv.solve()[1]
                    self.results[i] = val
                max_val = max(max_val, val)

        return max_val
