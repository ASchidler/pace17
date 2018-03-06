

class LabelStore:
    def __init__(self):
        self.ze = LabelNode(1, 0)
        self.on = LabelNode(1, 1)

    def append(self, val):
        if (val & 1) > 0:
            self.on.add(val)
        else:
            self.ze.add(val)

    def get(self, set_id):
        return LabelStoreIter(self, set_id)


class LabelNode:
    def __init__(self, depth, target):
        self.ze = None
        self.on = None
        self.val = None
        self.depth = depth
        self.initialized = False
        self.target = target

    def add(self, val):
        if not self.initialized:
            self.val = val
            self.initialized = True
        else:
            if self.val is not None and self.val != self.target:
                self.move_val(self.val)
                self.val = None
            if val == self.target:
                self.val = val
            else:
                self.move_val(val)

    def move_val(self, val):
        if val & (1 << self.depth) > 0:
            if self.on is None:
                self.on = LabelNode(self.depth + 1, (1 << (self.depth+1)) + self.target)
            self.on.add(val)
        else:
            if self.ze is None:
                self.ze = LabelNode(self.depth + 1, self.target)
            self.ze.add(val)


class LabelStoreIter:
    def __init__(self, store, set_id):
        self.store = store
        self.set_id = set_id
        self.queue = []
        if (1 & set_id) == 0:
            self.queue.append(store.on)

        self.next_node = store.ze

    def __iter__(self):
        return self

    def next(self):
        while self.next_node is not None or len(self.queue) > 0:
            if self.next_node is None:
                current_node = self.queue.pop()
            else:
                current_node = self.next_node

            self.next_node = current_node.ze

            if current_node.on is not None and (self.set_id & (1 << current_node.depth)) == 0:
                self.queue.append(current_node.on)

            if current_node.val is not None:
                return current_node.val

        raise StopIteration()

