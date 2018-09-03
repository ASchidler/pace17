import networkx as nx
from sys import maxint
import itertools as it
from structures import union_find as uf, steiner_graph as sg

"""Tries to split the graph into two parts that can be solved separately. Originally this has only be done for 
articulation points. The generalization of separators of larger size is from Polak and Maziarz' submission"""


def _find_articulation_points(steiner, blocked):
    """Finds all articulation points in the graph."""
    # This was originally a recursive algorithm found at https://www.geeksforgeeks.org/bridge-in-a-graph/
    # Since with larger instances the maximum recursion became a problem, this is now iterative

    visited = set()  # Do not visit a node twice
    low = CmDictionary(maxint)  # Minimum discovered time among the subnodes
    discovered = CmDictionary(maxint)  # "Time" a node has been expanded
    parent = CmDictionary(-1)  # Order of processing
    points = []
    stack = []  # Call stack for DFS

    for n in nx.nodes(steiner.graph):
        if n not in visited and n not in blocked:
            stack.append(([n], None))

            # Here the DFS begins
            while len(stack) > 0:
                us, p = stack.pop()

                # In this case, all subnodes have been processed. In the recursive case, this is the return
                if len(us) == 0:
                    ux = parent[p]
                    vx = p
                    low[ux] = min(low[ux], low[vx])

                    # Is a bridge?
                    if low[vx] >= discovered[ux]:
                        points.append(ux)
                else:
                    u = us.pop()
                    stack.append((us, p))
                    if u in visited:
                        if u != parent[p]:
                            low[p] = min(low[p], discovered[u])
                    else:
                        parent[u] = p
                        low[u] = len(visited)
                        discovered[u] = low[u]
                        visited.add(u)
                        stack.append((set(nx.neighbors(steiner.graph, u)).difference(blocked), u))

    return points


def _find_articulation_sets(steiner, s, blocked=set()):
    """Finds articulation sets, i.e. vertex sets that introduce a cut of size s"""
    c_min = (0, None, None)

    # Simply find points
    if s == 1:
        # Keeps track if a component has been removed. Causes a recomputation
        removed = True

        while removed:
            removed = False
            c_min = (0, None, None)
            points = _find_articulation_points(steiner, blocked)

            for ap in points:
                if steiner.graph.has_node(ap):
                    # Find the different components the AP cuts the graph
                    comp = uf.UnionFind(steiner.graph.nodes)
                    for (up, vp) in steiner.graph.edges:
                        if up != ap and up not in blocked and vp != ap and vp not in blocked:
                            comp.union(up, vp)

                    # Remove empty, this should be taken care of by other reductions
                    if ap not in steiner.terminals and len(blocked) == 0:
                        with_root = set()
                        for t in steiner.terminals:
                            with_root.add(comp.find(t))

                        rm_lst = []
                        for n in steiner.graph.nodes:
                            if comp.find(n) not in with_root and n != ap:
                                rm_lst.append(n)

                        if len(rm_lst) > 0:
                            removed = True
                            for n in rm_lst:
                                steiner.remove_node(n)

                            continue

                    # Separate this into two parts, keep first component and merge all others to get 2 parts
                    parts = [set(), set()]
                    first_root = None
                    for n in steiner.graph.nodes:
                        if n != ap and n not in blocked:
                            if first_root is None:
                                first_root = comp.find(n)

                            if comp.find(n) == first_root:
                                parts[0].add(n)
                            else:
                                parts[1].add(n)

                    # Check how many terminals are in each part. Keep the cut that separates terminals best
                    min_t = maxint
                    for c_p in parts:
                        t_count = len(c_p.intersection(steiner.terminals))
                        min_t = min(min_t, t_count)

                    if min_t > c_min[0]:
                        c_min = (min_t, parts, blocked.union({ap}))

    # s > 1
    else:
        # Try all vertices as part of the set, find APs given that the current vertex is not in the graph
        if len(blocked) == 0:
            for n in nx.nodes(steiner.graph):
                result = _find_articulation_sets(steiner, s - 1, {n})
                if result[0] > c_min[0]:
                    c_min = result
        # If we already have a vertex in the set, reduce calculations
        else:
            for n in range(1, min(blocked)):
                if n in steiner.graph.nodes:
                    result = _find_articulation_sets(steiner, s - 1, blocked.union({n}))
                    if result[0] > c_min[0]:
                        c_min = result

    return c_min


def _compute_partial_solutions(steiner, min_ap, rec):
    """Takes an articulation set and calculates the partial solutions returning the best.
    rec is a function to compute a solution for a steiner tree"""

    t_count, parts, aps = min_ap
    l_aps = list(aps)
    best_sol = (None, maxint)

    # For all subsets of aps
    for c_mask in range(1, (1 << len(aps))):
        c_terms = []
        for i in range(0, len(aps)):
            if ((1 << i) & c_mask) > 0:
                c_terms.append(l_aps[i])

        c_terms.sort()

        checked_none = False
        checked_all = False

        # The combination permutations and join_in_left that covers all possible combinations of sub solutions
        for p_terms in it.permutations(c_terms):
            if p_terms[0] > p_terms[len(p_terms) - 1]:
                continue

            full_mask = (1 << (len(p_terms) - 1)) - 1

            # Empty and full subset are the same no matter the permutation, calculate only once
            for join_in_left in range(0, full_mask + 1):
                # Avoid duplicate calculation
                if join_in_left == 0:
                    if checked_none:
                        continue
                    checked_none = True
                elif join_in_left == full_mask:
                    if checked_all:
                        continue
                    checked_all = True

                sol = []

                # Calculate the two partial solutions given the current loop variables
                for part_id in range(0, 2):
                    join_here = join_in_left if part_id == 0 else join_in_left ^ full_mask
                    c_part = parts[part_id]

                    g = sg.SteinerGraph()

                    # Maps cut vertices to another one. Given more than one AP the partial solutions cannot be connected
                    # (otherwise there would be a cycle). To make them connected some APs are merged so they appear as
                    # one to the solver making the solution connected. It is split afterwards to create the final sol
                    def map_node(us):
                        if us in p_terms:
                            idx = p_terms.index(us)
                            while idx > 0 and (join_here & (1 << (idx - 1))) == 1:
                                idx = idx - 1

                            return p_terms[idx]
                        elif us in aps:
                            return us
                        elif us in c_part:
                            return us

                        return -1

                    # Add edges to current subgraph. Keep track of mapped edges to restore them in the solution
                    mapped = []
                    for (u, v, d) in steiner.graph.edges(data='weight'):
                        up = map_node(u)
                        vp = map_node(v)

                        if up != vp and up != -1 and vp != -1:
                            g.add_edge(up, vp, d)
                            if up != u or vp != v:
                                mapped.append(((up, vp, d), (u, v, d)))

                    # May happen if a vertex split the graph in more than one component
                    if not nx.is_connected(g.graph):
                        break

                    # Add terminals
                    for t in steiner.terminals.union(p_terms):
                        t = map_node(t)
                        if t in g.graph.nodes:
                            g.terminals.add(t)

                    # Find solution and unmap edges
                    part_sol = rec(g)

                    for ((u1, v1, d1), (u2, v2, d2)) in mapped:
                        if part_sol[0].has_edge(u1, v1) and part_sol[0][u1][v1]['weight'] == d1:
                            part_sol[0].remove_edge(u1, v1)
                            part_sol[0].add_edge(u2, v2, weight=d2)

                    sol.append(part_sol)

                # Combine partial solutions
                if len(sol) == 2:
                    val = sol[0][1] + sol[1][1]
                    if val < best_sol[1]:
                        best_sol = (nx.compose(sol[0][0], sol[1][0]), val)

    return best_sol


def decompose(steiner, sol, rec, debug=False):
    """Tries to decompose the graph into subgraphs and calculates the solution. sol is a function that
    calculates the solution for the current graph, rec is a function that calculates the solutions for a new
    graph"""

    c_min = (0, None, None)
    # Used to avoid infeasible splitting and therefore long computation times
    edge_limit = [maxint, 3000, 1000]
    term_limit = [1, 5, 8]

    # Limit to articulation sets of size 3.
    for s in range(1, 4):
        if c_min[0] > 0 or len(steiner.graph.nodes) < 4 or len(steiner.graph.edges) > edge_limit[s-1]:
            break

        c_min = _find_articulation_sets(steiner, s)

    # Enforce cut size. This is necessary to avoid infeasibly small cuts
    if c_min[0] == 0 or c_min[0] < term_limit[len(c_min[2]) - 1]:
        return sol(steiner)

    if debug:
        print "Splitting problem. Using set of size {} splitting the problem into parts of {} and {}"\
            .format(len(c_min[2]), len(c_min[1][0]), len(c_min[1][1]))

    return _compute_partial_solutions(steiner, c_min, rec)


class CmDictionary(dict):
    def __init__(self, default):
        super(CmDictionary, self).__init__()
        self.default = default

    def __missing__(self, key):
        return self.default
