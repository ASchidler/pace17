class UnionFind:
    class _UfElement:
        def __init__(self, val):
            self.val = val
            self.rank = 0
            self.size = 1
            self.parent = self

    def __init__(self, lst):
        self._els = {e: self._UfElement(e) for e in lst}

    def _find(self, val):
        el = self._els[val]
        while el.parent != el:
            el = el.parent

        return el

    def find(self, val):
        return self._find(val).val

    def union(self, val1, val2):
        el1 = self._find(val1)
        el2 = self._find(val2)

        if el1 == el2:
            return False

        if el1.rank < el2.rank:
            el1, el2 = el2, el1

        el2.parent = el1
        if el1.rank == el2.rank:
            el1.rank = el1.rank + 1

        return True
