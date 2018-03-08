import set_storage as stor
import time

storage = stor.SetStorage()
storage2 = []

storage.add(127)
storage.add(128)
storage.add(255)
storage.add(126)

for x in storage.findAll(1):
    print x


for x in xrange(1 << 22):
    storage.add(x)
    storage2.append(x)

start1 = time.time()

for z in storage.findAll(0):
    pass

print "Run1: {}".format(time.time() - start1)
start2 = time.time()
for z in storage2:
    pass

print "Run2: {}".format(time.time() - start2)

set_id = 33648
start3 = time.time()
for z in storage.findAll(set_id):
    pass

print "Run3: {}".format(time.time() - start3)
start4 = time.time()
for z in storage2:
    if (set_id & z) == 0:
        pass

print "Run4: {}".format(time.time() - start4)

start5 = time.time()
for z in storage.findAllGen(set_id):
    pass
print "Run5: {}".format(time.time() - start5)