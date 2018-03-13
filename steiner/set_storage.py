class SetStorage:
    def __init__(self, cnt):
        self.initialized = False
        self._nodes = {}
        self.add = self.first_add
        self.cnt = cnt + 1

    def first_add(self, set_id):
        self.initialized = True
        self._nodes[0] = (set_id, False, 0)
        self.add = self.other_add

    def other_add(self, set_id):
        current_node_id = 0
        current_value = set_id
        current_level = 0
        current_target = 1
        placed = False

        while not placed:
            if current_node_id not in self._nodes:
                self._nodes[current_node_id] = (current_value, current_value == current_target, current_level)
                placed = True
            else:
                current_node = self._nodes[current_node_id]

                if not current_node[1]:
                    if current_value == current_target:
                        # Special root node handling, root node should never be fixed (no information)
                        self._nodes[current_node_id] = (current_target, current_node_id != 0, current_level)
                        current_value = current_node[0]
                    else:
                        parity_old = bin(current_node[0]).count("1")
                        parity_new = bin(current_value).count("1")

                        if parity_new < parity_old:
                            self._nodes[current_node_id] = (current_value, False, current_level)
                            current_value = current_node[0]

                terminal = 1 << current_level
                current_level += 1
                if (terminal & current_value) > 0:
                    current_node_id = 2 * current_node_id + 1
                    current_target = current_target | terminal
                else:
                    current_node_id = 2 * current_node_id + 2
                    current_target = current_target ^ terminal | (terminal << 1)

    def find_all(self, set_id):
        if self.initialized:
            nodes = self._nodes
            # Array of set bits, extend it so it matches the length of terminals
            level_set = map(lambda x: x == "1", bin(set_id))
            level_set.reverse()
            level_set.extend([False] * (self.cnt - len(level_set)))

            current_node_id = 0
            queue = []

            # Special case for root node, since no information from the previous node is available
            while 1:
                try:
                    c_root = nodes[current_node_id]
                except KeyError:
                    break

                stepping = (2 * current_node_id) + 2 - current_node_id
                for c_sub in xrange(0, self.cnt):
                    c_id = current_node_id + ((1 << c_sub) - 1) * stepping

                    try:
                        val = nodes[c_id]
                        if (val[0] & set_id) == 0:
                            yield val[0]
                    except KeyError:
                        break

                # Add the one branch if the bit is not set
                if not level_set[c_root[2]]:
                    current_node_id = 2 * current_node_id + 1
                else:
                    break


class DebuggingSetStorage(SetStorage):
    """This adds self checks to the set storage. It is very slow and its use is to test changes, for
    production use, use the base storage"""

    def __init__(self, cnt):
        self._check = []
        SetStorage.__init__(self, cnt)
        self.add = self._initial_add

    def _health_check(self, n_id, bit_set):
        n = self._nodes.get(n_id)
        if n is None:
            return

        if n[2] > 0:
            result = n[0] & (1 << (n[2] - 1))
            if result > 0 and not bit_set:
                print "!!! Set where 0"
            elif result == 0 and bit_set:
                print "!!! Unset where 1"

        self._health_check(n_id * 2 + 2, False)
        self._health_check(n_id * 2 + 1, True)

    def _initial_add(self, set_id):
        self._check.append(set_id)
        self.first_add(set_id)
        self.add = self._add

    def _add(self, set_id):
        self._check.append(set_id)
        self.other_add(set_id)

    def find_all(self, set_id):
        if self.initialized:
            if self._nodes[0][1]:
                print "*** Root node should never be fixed"
                raise StandardError
            self._health_check(0, (1 & self._nodes[0][0]) > 0)
            ref = list(SetStorage.find_all(self, set_id))
            ref2 = set([x for x in self._check if (set_id & x) == 0])
            if len(ref) != len(ref2):
                print "*** Length Error {} to {}".format(len(ref), len(ref2))
                raise StandardError
            for x in ref:
                if x not in ref2:
                    print "*** Content Error {}".format(x)
                    raise StandardError

            for x in ref:
                yield x
