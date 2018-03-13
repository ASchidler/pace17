class SetStorage:
    """A storage for sets that can quickly retrieve disjoint sets for a given set"""

    # Empty since it will be overridden
    def add(self, set_id):
        """Adds a value to the collection"""
        pass

    def __init__(self, cnt):
        self.initialized = False
        self._nodes = {}
        self.add = self._first_add
        self.cnt = cnt + 1

    def _first_add(self, set_id):
        """ Adds the first value. Additional checks are skipped"""
        self.initialized = True
        self._nodes[0] = set_id
        self.add = self._other_add

    def _other_add(self, set_id):
        """ Adds every value but the first and restructures collection as needed"""
        current_node_id = 0
        current_value = set_id
        current_level = 0
        current_target = 1
        placed = False

        # Try to place the value
        while not placed:
            # If we have a non-existing node, we can place the value
            if current_node_id not in self._nodes:
                self._nodes[current_node_id] = current_value
                placed = True
            # Determine if the current value of the node or the new value is placed in the current node
            else:
                current_node = self._nodes[current_node_id]

                # If the node already has the target value, do not change
                if not current_node == current_target:
                    # If the new value has the target value, place
                    if current_value == current_target:
                        self._nodes[current_node_id] = current_target
                        current_value = current_node
                    # Otherwise the lower parity stays (higher likelihood to be disjoint)
                    else:
                        parity_old = bin(current_node).count("1")
                        parity_new = bin(current_value).count("1")

                        if parity_new < parity_old:
                            self._nodes[current_node_id], current_value = current_value, current_node

                # Place the value
                terminal = 1 << current_level
                current_level += 1
                # If the current bit of the value is set branch left, otherwise branch right
                if (terminal & current_value) > 0:
                    current_node_id = 2 * current_node_id + 1
                    # The new target is the set plus the current terminal
                    current_target = current_target | terminal
                else:
                    current_node_id = 2 * current_node_id + 2
                    # The new target is the set without the current terminal and with the next terminal
                    current_target = current_target ^ terminal | (terminal << 1)

    def find_all(self, set_id):
        """" Returns all stored sets that are disjoint from the given set"""

        if self.initialized:
            nodes = self._nodes
            # Array of set bits, extend it so it matches the length of terminals
            level_set = map(lambda x: x == "1", bin(set_id))
            level_set.reverse()
            level_set.extend([False] * (self.cnt - len(level_set)))

            # Special case for the root node
            ids = [0]
            if (nodes[0] & set_id) == 0:
                yield nodes[0]

            # Now traverse the tree level by level, always expanding the selected node from the previous level
            for c_level in xrange(1, self.cnt):
                if not level_set[c_level - 1]:
                    # Add one and zero branches
                    ids = [2 * i + o for i in ids for o in [1, 2] if (2 * i + o) in nodes]
                else:
                    # Only zero branches
                    ids = [2 * i + 2 for i in ids if (2 * i + 2) in nodes]

                # Now check if the values are disjoint
                for val in (nodes[i] for i in ids):
                    if (val & set_id) == 0:
                        yield val


class DebuggingSetStorage(SetStorage):
    """This adds self checks to the set storage. It is very slow and its use is to test changes, for
    production use, use the base storage"""

    def __init__(self, cnt):
        self._check = []
        SetStorage.__init__(self, cnt)
        self.add = self._initial_add

    def _health_check(self, n_id, bit_set, lvl):
        """ Checks if the position of the values in the tree is valid"""
        n = self._nodes.get(n_id)
        if n is None:
            return

        if lvl > 0:
            result = n & (1 << (lvl - 1))
            if result > 0 and not bit_set:
                print "!!! Set where 0"
            elif result == 0 and bit_set:
                print "!!! Unset where 1"

        self._health_check(n_id * 2 + 2, False, lvl + 1)
        self._health_check(n_id * 2 + 1, True, lvl + 1)

    def _initial_add(self, set_id):
        """Used to override the initial add in the base class"""
        self._check.append(set_id)
        self._first_add(set_id)
        self.add = self._add

    def _add(self, set_id):
        """Used to override the other add in the base class"""
        self._check.append(set_id)
        self._other_add(set_id)

    def find_all(self, set_id):
        """Finds all disjoint sets and performs a consistency check on the colleciton"""
        if self.initialized:
            # Check positions in the tree
            self._health_check(0, (1 & self._nodes[0]) > 0, 0)
            # Verify that all disjoint values are returned
            ref = list(SetStorage.find_all(self, set_id))
            ref2 = set([x for x in self._check if (set_id & x) == 0])
            if len(ref) != len(ref2):
                print "*** Length Error {} to {}".format(len(ref), len(ref2))
                raise StandardError
            for x in ref:
                if x not in ref2:
                    print "*** Content Error {}".format(x)
                    raise StandardError

            # Return results
            for x in ref:
                yield x
