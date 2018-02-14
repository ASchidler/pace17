import steiner.steiner_graph as st

""" Parses files with the PACE file format"""


def parse_graph(line, steiner):
    lst = line.split(' ')
    if line.startswith("e "):
        steiner.graph.add_edge(int(lst[1]), int(lst[2]), weight=int(lst[3]))


def parse_terminal(line, steiner):
    lst = line.split(' ')
    if line.startswith('t '):
        steiner.graph.node[int(lst[1])]['terminal'] = True
        steiner.terminals.add(int(lst[1]))


def parse_file(f):
    # 0 is start, 1 is graph, 2 are terminals, 3 are decompositions
    parse_mode = 0

    steiner = st.SteinerGraph()

    for line in f:
        line = line.strip().lower()
        if line.startswith("end"):
            parse_mode = 0
        elif line.startswith("section graph"):
            parse_mode = 1
        elif line.startswith("section terminals"):
            parse_mode = 2
        elif line.startswith("section tree decomposition"):
            parse_mode = 3
        elif parse_mode == 1:
            parse_graph(line, steiner)
        elif parse_mode == 2:
            parse_terminal(line, steiner)

    # Otherwise ignore

    f.close()

    return steiner

