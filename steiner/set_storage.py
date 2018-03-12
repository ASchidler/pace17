class SetStorage:
    def __init__(self):
        self.root = _SetNode(1, 0)
        self.initialized = False

    def add(self, set_id):
        self.initialized = True
        self.root.add(set_id)

    def findAllGen(self, set_id):
        if self.initialized:
            queue = []
            pop = queue.pop
            append = queue.append

            current_node = (self.root, (set_id & 1) > 0)

            # Special case for root node, since no information from the previous node is available
            while current_node[0] is not None or len(queue) > 0:
                if current_node[0] is None:
                    current_node = pop()
                    if current_node[0] is None:
                        continue

                next_level_set = (set_id & (1 << (current_node[0].level + 1)))

                if (not current_node[1] and current_node[0].fixed) or (current_node[0].val & set_id) == 0:
                    yield current_node[0].val

                if not current_node[1]:
                    append((current_node[0].on, next_level_set))

                current_node = (current_node[0].zer, next_level_set)


class _SetNode:
    def __init__(self, target, level):
        self.on = None
        self.zer = None
        self.val = None
        self.target = target
        self.fixed = False
        self.level = level

    def add(self, val):
        if self.val is None:
            self.val = val

        else:
            pass_on = None
            # Duplicate check should not be necessary
            if self.val is None:
                self.val = val
                if val == self.target:
                    self.fixed = True
            elif self.fixed:
                pass_on = val
            elif val == self.target:
                pass_on, self.val = self.val, val
                self.fixed = True
            else:
                parity_old = bin(self.val).count("1")
                parity_new = bin(val).count("1")

                if parity_new < parity_old:
                    pass_on, self.val = self.val, val
                else:
                    pass_on = val

            # Special root node handling. Since at the evaluation nothing is known about the first bit, this is necessary
            if self.level == 0:
                self.fixed = False

            if pass_on is not None:
                terminal = 1 << self.level
                if (terminal & pass_on) > 0:
                    if self.on is None:
                        self.on = _SetNode(self.target | terminal, self.level + 1)
                    self.on.add(pass_on)
                else:
                    if self.zer is None:
                        # Zero node targets are built negating the current bit and setting the next one
                        self.zer = _SetNode((self.target ^ terminal) | (terminal << 1), self.level + 1)
                    self.zer.add(pass_on)

class DebuggingSetStorage(SetStorage):
    """This adds self checks to the set storage. It is very slow and its use is to test changes, for
    production use, use the base storage"""

    def __init__(self):
        self._check = []
        SetStorage.__init__(self)

    def _health_check(self, n, bit_set):
        if n is None:
            return

        if n.level > 0:
            result = n.val & (1 << (n.level - 1))
            if result > 0 and not bit_set:
                print "!!! Set where 0"
            elif result == 0 and bit_set:
                print "!!! Unset where 1"

        self._health_check(n.zer, False)
        self._health_check(n.on, True)

    def add(self, set_id):
        self._check.append(set_id)
        SetStorage.add(self, set_id)

    def findAllGen(self, set_id):
        if self.initialized:
            ref = list(SetStorage.findAllGen(self, set_id))
            ref2 = set([x for x in self._check if (set_id & x) == 0])
            if len(ref) != len(ref2):
                print "*** Length Error {} to {}".format(len(ref), len(ref2))
                raise StandardError
            for x in ref:
                if x not in ref2:
                    print "*** Content Error {}".format(x)
                    raise StandardError

            self._health_check(self.root, (1 & self.root.val) > 0)

            for x in ref:
                yield x





