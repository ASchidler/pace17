import steiner.steiner_graph as st

""" Parses files with the PACE file format"""


def parse_graph(line, steiner):
    lst = line.split(' ')
    if line.startswith("E "):
        steiner.graph.add_edge(int(lst[1]), int(lst[2]), weight=int(lst[3]))


def parse_terminal(line, steiner):
    lst = line.split(' ')
    if line.startswith('T '):
        steiner.graph.node[int(lst[1])]['terminal'] = True
        steiner.terminals.add(int(lst[1]))


def parse_file(filename):
    f = open(filename, "r")
    # 0 is start, 1 is graph, 2 are terminals, 3 are decompositions
    parse_mode = 0

    steiner = st.SteinerGraph()

    for line in f:
        line = line.strip()
        if line.startswith("END"):
            parse_mode = 0
        elif line.startswith("SECTION Graph"):
            parse_mode = 1
        elif line.startswith("SECTION Terminals"):
            parse_mode = 2
        elif line.startswith("SECTION Tree Decomposition"):
            parse_mode = 3
        elif parse_mode == 1:
            parse_graph(line, steiner)
        elif parse_mode == 2:
            parse_terminal(line, steiner)

    # Otherwise ignore

    f.close()

    return steiner

