import networkx as nx


def parse(solution):
    if solution is not None:
        print "VALUE " + str(solution[1])

        for (u, v) in nx.edges(solution[0]):
            print "{} {}".format(u, v)
