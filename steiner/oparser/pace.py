"""Output conforming to PACE guidelines"""


def parse(solution):
    if solution is not None:
        print "VALUE " + str(solution[1])

        for (u, v) in solution[0].edges:
            print "{} {}".format(u, v)
