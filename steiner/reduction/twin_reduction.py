
class TwinReductions:

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.nodes) > 500 or len(steiner.graph.edges) / len(steiner.graph.nodes) > 10:
            return 0

        track = len(steiner.graph.edges)
        nb = steiner.graph._adj

        for n in list(steiner.graph.nodes):
            if not steiner.graph.has_node(n):
                continue

            n_nb = set(nb[n].keys())

            for n2 in list(steiner.graph.nodes):
                if n < n2:
                    n2_nb = set(nb[n2].keys())
                    found = False

                    try:
                        n_nb.remove(n2)
                        found = True
                    except KeyError:
                        pass

                    try:
                        n2_nb.remove(n)
                    except KeyError:
                        pass

                    set1, set2, smaller_node = None, None, None

                    if n2_nb.issubset(n_nb) and n2 not in steiner.terminals:
                        set1, set2 = n2_nb, n_nb
                        smaller_node, bigger_node = n2, n
                    elif n_nb.issubset(n2_nb) and n not in steiner.terminals:
                        set1, set2 = n_nb, n2_nb
                        smaller_node, bigger_node = n, n2

                    if set1 is not None and len(set1) > 0:
                        all_true = all(nb[bigger_node][x1]['weight'] <= nb[smaller_node][x1]['weight'] for x1 in set1)
                        if all_true:
                            steiner.remove_node(smaller_node)
                            if smaller_node == n:
                                break

                    if found:
                        n_nb.add(n2)

        return track - len(steiner.graph.edges)

    def post_process(self, solution):
        return solution, False