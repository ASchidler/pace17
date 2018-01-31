import networkx as nx


# Removed nodes with degree 1 (non-terminal) and merges nodes with degree 2
class DegreeReduction:

    def reduce(self, steiner):
        d1 = 0
        d2 = 0

        for n, degree in nx.degree(steiner.graph):
            if degree == 1 and n not in steiner.terminals:
                d1 = d1 + 1
            elif degree == 2 and n not in steiner.terminals:
                d2 = d2 + 1

        print "Degree 1 " + str(d1)
        print "Degree 2 " + str(d2)
