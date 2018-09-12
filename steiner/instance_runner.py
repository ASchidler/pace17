import iparser as pp
import sys
import solving_package as sp

""" This runner is used to run certain instances in debug mode. It is mainly used manually, i.e. edited and then run """


def process_file(filename, solve, apply_reductions):
    """ Processes a file. Parses, reduces and solves it. Includes verbose oparser"""

    f = open(filename, "r")
    steiner = pp.parse_pace_file(f)
    sp.run(steiner, sp.SolvingConfig(debug=True, solve=solve, apply_reductions=apply_reductions, verify=True,
                                     print_output=True))


# Instances that are not solvable yet
hard_instances = [161, 162, 163, 164, 165, 171, 172, 173, 194, 195, 196, 200]
# Solvable but at the upper end of the time limit
long_runtime = [150, 152, 167, 187, 189, 190, 192, 193, 197, 198, 199]
# All other instances are solvable in a feasible amount of time
easy_instances = [i for i in xrange(1, 200) if i not in hard_instances and i not in long_runtime]
solvable = list(easy_instances)
solvable.extend(long_runtime)

# 16x 0640/40896, almost no reductions
# 171 0243/01215, few reductions, unit weights
# 173 0243/01215, no reductions, most edges weight 1, some 2
# 195 0550/05000, no reductions, unit weights
# Not 160, 162 (u), 164(u), 190, 196
# Yes 2-160, 166, 168, 170, 174-188, 192,
# ? 200, 172, 194
# slow 198
#for i in [171]: # [171, 173, 195]:# (x for x in lst if x > 189): # hard_instances:
for i in [200]:
    file_path = "..\instances\lowTerm\instance{0:03d}.gr"

    sys.setcheckinterval(1000)
    current_file = file_path.format(i)
    print current_file
    process_file(current_file, True, True)

