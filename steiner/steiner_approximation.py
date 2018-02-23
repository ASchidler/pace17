import sys
import networkx as nx


class SteinerApproximation:
    """Represents an approximation algorithm for steiner trees for an upper bound. It applies repeated shortest paths"""
    def __init__(self, steiner):
        self.cost = sys.maxint
        self.tree = None

        # TODO: Find a more sophisticated selection strategy?
        for i in range(0, min(10, len(steiner.terminals))):
            result = self.calculate(steiner, i)
            if result[1] < self.cost:
                self.cost = result[1]
                self.tree = result[0]

    def calculate(self, steiner, start):
        # Solution init
        tree = nx.Graph()
        cost = 0

        # Queue -> all terminals must be in solutions and processed nodes
        queue = sorted(list(steiner.terminals))
        nodes = set()

        # Set start node
        nodes.add(queue.pop(start))

        while len(queue) > 0:
            # Find terminal with minimal distance to tree
            min_val = sys.maxint
            min_t = None
            min_n = None

            for t in queue:
                for n in nodes:
                    c = steiner.get_lengths(n, t)

                    if c < min_val:
                        min_val = c
                        min_t = t
                        min_n = n

            # Add to solution
            nodes.add(min_t)
            queue.remove(min_t)

            # Find shortest path between
            path = nx.dijkstra_path(steiner.graph, min_t, min_n)

            # Now backtrack edges
            prev_n = min_t
            for i in range(1, len(path)):
                current_n = path[i]
                if not tree.has_edge(prev_n, current_n):
                    nodes.add(current_n)
                    w = steiner.graph[prev_n][current_n]['weight']
                    cost = cost + w
                    tree.add_edge(prev_n, current_n, weight=w)

                prev_n = current_n

        # Improve solution by creating an MST and deleting non-terminal leafs
        tree = nx.minimum_spanning_tree(tree)

        # Remove non-terminal leafs
        old = sys.maxint
        while old != len(nx.nodes(tree)):
            old = len(nx.nodes(tree))

            for (n, d) in list(nx.degree(tree)):
                if d == 1 and n not in steiner.terminals:
                    tree.remove_node(n)

        # Calculate cost
        cost = 0
        for (u, v, d) in list(tree.edges(data='weight')):
            cost = cost + d

        return tree, cost
