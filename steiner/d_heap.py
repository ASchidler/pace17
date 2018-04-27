
def create_queue(d):
    return [], {}, d

def _bubble_up(ls, e, d, idx):
    n_val = ls[idx]

    # Bubble value up the tree
    while idx > 0:
        n_idx = (idx - 1) / d

        # if current node is bigger, swap
        if ls[n_idx][0] > n_val[0]:
            ls[idx] = ls[n_idx]
            e[ls[n_idx][1]] = idx
            idx = n_idx
            continue
        break

    # This may reduce the number of set operations, set values at the end
    ls[idx] = n_val
    e[n_val[1]] = idx


def enqueue(queue, priority, key):
    ls, e, d = queue

    # Check if value already exists
    if key in e:
        idx = e[key]
        if ls[idx][0] <= priority:
            return
        else:
            ls[idx][0] = priority
    else:
        idx = len(ls)
        ls.append([priority, key])

    _bubble_up(ls, e, d, idx)


def dequeue(queue):
    ls, e, d = queue

    # Swap last und first value. Remove last value
    val = ls[0]
    n_val = ls.pop()
    e.pop(val[1])
    if not ls:
        return val[1]

    ls[0] = n_val

    # Push element down to a leaf
    idx = 0
    end = len(ls)
    child = 1

    # Iterate until leaf is found
    while child < end:
        c_idx = child
        stop = min(end, child + d)
        child += 1

        # Find smallest child
        while child < stop:
            if ls[child][0] < ls[c_idx][0]:
                c_idx = child
            child += 1

        # Move minimum item up one level
        ls[idx] = ls[c_idx]
        e[ls[c_idx][1]] = idx
        idx = c_idx
        child = d * idx + 1

    # Let element bubble up. As the element was the last it is usually large
    # on average putting it at a leaf and bubbling up needs fewer comparisons
    ls[idx] = n_val
    e[n_val[1]] = idx
    _bubble_up(ls, e, d, idx)

    return val[1]
