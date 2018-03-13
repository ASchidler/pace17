import set_storage as stor
import time

storage = stor.SetStorage(32)
storage2 = []

storage.add(127)
storage.add(128)
storage.add(255)
storage.add(126)

for x in xrange(1 << 22):
    storage.add(x)
    storage2.append(x)

start1 = time.time()

for z in storage.find_all(0):
    pass

print "Class all: {}".format(time.time() - start1)
start2 = time.time()
for z in storage2:
    pass

print "List all: {}".format(time.time() - start2)

set_id = 33648

start4 = time.time()
for z in storage2:
    if (set_id & z) == 0:
        pass

print "List disjunct: {}".format(time.time() - start4)

start5 = time.time()
for z in storage.find_all(set_id):
    pass
print "Class disjunct: {}".format(time.time() - start5)

start6 = time.time()
for z in filter(lambda x: (x & z) == 0, storage2):
    pass

print "Filter disjunct: {}".format(time.time() - start6)
