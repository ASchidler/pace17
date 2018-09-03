from sys import maxint

"""This manages a list as a priority queue using buckets. The idea is that with a low upper bound, it may be more
efficient to use buckets than a heap"""


def create_queue(bound):
    q = [set() for _ in xrange(0, bound + 2)]
    # Queue, Bucket pointers, Current Minimum as a "reference object"
    return q, {}, [maxint]


def enqueue(queue, priority, key):
    ls, e, q_min = queue

    # If existing and smaller, move item up
    if key in e:
        if priority < e[key]:
            ls[e[key]].remove(key)
            ls[priority].add(key)
            e[key] = priority
    # Add to bucket
    else:
        ls[priority].add(key)
        e[key] = priority

    # Adjust min pointer
    q_min[0] = min(q_min[0], priority)


def dequeue(queue):
    ls, e, q_min = queue

    # Get smallest object
    c_min = q_min[0]

    # If bucket is empty, move pointer up. Do this here and not afterwards as an intermediate enqueue might do the work
    if not ls[c_min]:
        lenl = len(ls)
        i = c_min + 1
        for i in xrange(c_min + 1, lenl):
            if ls[i]:
                break

        q_min[0] = i
        c_min = i

    val = ls[c_min].pop()
    e.pop(val)

    return val