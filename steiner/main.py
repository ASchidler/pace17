import networkx as nx
import sys
import os.path
import steiner_graph as sg
import time
import solver_2k as sv

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <file>"
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print "File does not exist"
    sys.exit()


def process_file(filename):
    graph = sg.SteinerGraph()
    graph.parse_file(filename)

    solver = sv.Solver2k(graph)
    solver.solve()
    return

    # Degree check
    d1 = 0
    d2 = 0

    for n, degree in nx.degree(graph.graph):
        if degree == 1 and n not in graph.terminals:
            d1 = d1 + 1
        elif degree == 2 and n not in graph.terminals:
            d2 = d2 + 1

    print "Degree 1 " + str(d1)
    print "Degree 2 " + str(d2)

    # Incidence check
    incidence = 0
    for t in graph.terminals:
        min_val = sys.maxint
        min_node = None
        neighbors = 0

        for n in nx.neighbors(graph.graph, t):
            neighbors = neighbors + 1
            w = graph.graph[t][n]['weight']
            if w < min_val:
                min_node = n
                min_val = w

            if min_node in graph.terminals or neighbors == 1:
                incidence = incidence + 1

    print "Incidence " + str(incidence)

    #Components
    if not nx.is_connected(graph.graph):
        for c in nx.connected_components(graph.graph):
            found = False
            for n in c:
                if n in graph.terminals:
                    found = True

            if not found:
                print "Found unconnected component of size " + str(len(c))
    else:
        print "Only one component found"

    # Terminal distance
    terminal_edges = 0
    max_val = 0
    for t1 in graph.terminals:
        min_val = sys.maxint
        for t2 in graph.terminals:
            if t1 != t2:
                dist = graph.get_lengths()[t1][t2]
                min_val = min(min_val, dist)

        if min_val != sys.maxint:
            max_val = max(max_val, min_val)

    for (u, v, d) in graph.graph.edges(data='weight'):
        if d > max_val:
            terminal_edges = terminal_edges + 1

    print "terminal edge " + str(terminal_edges)

    # Steiner edges
    sedges = 0
    for (u, v, d) in graph.graph.edges(data='weight'):
        if d > graph.get_steiner_lengths()[u][v]:
            sedges = sedges + 1

    print "Steiner edges " + str(sedges)

    # Ntdk
    ntdk_edge = 0
    for n in nx.nodes(graph.graph):
        neighbors = list(nx.all_neighbors(graph.graph, n))
        degree = len(neighbors)
        true_for_all = True

        if 2 < degree <= 4:
            # Powersets
            for power_set in range(1, 1 << degree):
                # Create complete graph
                power_graph = nx.Graph()
                edge_sum = 0
                for i in range(0, degree):
                    if ((1 << i) & power_set) > 0:
                        n1 = neighbors[i]
                        edge_sum = edge_sum + graph.graph[n][n1]['weight']

                        for j in range(i + 1, degree):
                            if ((1 << j) & power_set) > 0:
                                n2 = neighbors[j]
                                w = graph.get_steiner_lengths()[n1][n2]
                                power_graph.add_edge(n1, n2, weight=w)

                mst = list(nx.minimum_spanning_edges(power_graph))

                mst_sum = 0
                for edge in mst:
                    mst_sum = mst_sum + power_graph[edge[0]][edge[1]]['weight']

                true_for_all = true_for_all and mst_sum <= edge_sum

            if true_for_all:
                ntdk_edge = ntdk_edge + 1

    print "NTDK edges " + str(ntdk_edge)

    # Voronoi test
    voronoi_cnt = 0

    voronoi_areas = dict()
    for t in graph.terminals:
        voronoi_areas[t] = set()

    for n in nx.nodes(graph.graph):
        if n not in graph.terminals:
            min_val = sys.maxint
            min_node = None

            for t in graph.terminals:
                c = graph.get_lengths()[n][t]
                if c < min_val:
                    min_val = c
                    min_node = t

            voronoi_areas[min_node].add(n)

    # Exit nodes
    exit_sum = 0
    exit_max1 = 0
    exit_max2 = 0

    for (t, r) in voronoi_areas.items():
        min_val = sys.maxint
        for n in nx.nodes(graph.graph):
            if n not in r:
                min_val = min(min_val, graph.get_lengths()[t][n])

        exit_sum = exit_sum + min_val
        if min_val >= exit_max1:
            exit_max2 = exit_max1
            exit_max1 = min_val

    exit_sum = exit_sum - exit_max1 - exit_max2

    for (u, v, d) in graph.graph.edges(data='weight'):
        sum = 0
        cnt = 0
        if u in graph.terminals:
            cnt = cnt + 1
        if v in graph.terminals:
            cnt = cnt + 2

        for (t, r) in voronoi_areas.items():
            if u in r:
                sum = sum + graph.get_lengths()[u][t]
                cnt = cnt + 1

            if v in r:
                sum = sum + graph.get_lengths()[v][t]
                cnt = cnt + 1

        if d + sum + exit_sum > graph.get_approximation().cost:
            voronoi_cnt = voronoi_cnt + 1

    print "Voronoi " + str(voronoi_cnt)


    # Reachability

    reach_cnt = 0

    approx_nodes = nx.nodes(graph.get_approximation().tree)

    for n in nx.nodes(graph.graph):
        if n not in approx_nodes:
            min_val1 = sys.maxint
            min_val2 = sys.maxint
            max_val = 0

            for t in graph.terminals:
                d = graph.get_lengths()[t][n]
                if d <= min_val1:
                    min_val2 = min_val1
                    min_val1 = d

                max_val = max(max_val, d)

            if min_val + min_val2 + max_val > graph.get_approximation().cost:
                reach_cnt = reach_cnt + 1

    print "Reachability " + str(reach_cnt)


    # Cut reachability

    # Find smallest neighbours
    cut_cnt = 0
    terminal_minimums = {}

    for t in graph.terminals:
        min_val = sys.maxint

        for n in nx.neighbors(graph.graph, t):
            w = graph.graph[t][n]['weight']
            min_val = min(w,min_val)

        terminal_minimums[t] = min_val

    approx_nodes = nx.nodes(graph.get_approximation().tree)
    for n in nx.nodes(graph.graph):
        if n not in approx_nodes:
            min_val1 = sys.maxint
            min_val2 = sys.maxint
            n1 = None
            n2 = None

            for t in graph.terminals:
                d = graph.get_lengths()[t][n]
                diff = d - terminal_minimums[t]

                if diff <= min_val1:
                    min_val2 = min_val1
                    min_val1 = d
                    n1 = t
                    n2 = n

            min_sum = min_val1 + min_val2

            for t in graph.terminals:
                if t != n1 and t != n2:
                    min_sum = min_sum + terminal_minimums[t]

            if min_sum >= graph.get_approximation().cost:
                cut_cnt = cut_cnt + 1

    print "Cut Reachiability " + str(cut_cnt)


for i in range(1, 100):
    filename = "D:\steinertree\pace2017\instances\lowTerm\instance{0:03d}.gr"
    if i % 2 == 1:
        current_file = filename.format(i)
        print current_file
        start = time.time()
        process_file(current_file)
        print "Done in " + str (time.time() - start)
        print ""


