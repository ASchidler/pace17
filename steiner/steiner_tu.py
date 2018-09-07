import sys

import iparser as pp
import solving_package as sp

""" This script is used for PACE. It reads the instance from STDIN and has no extra output except the solution"""

steiner = pp.parse_pace_file(sys.stdin)
sp.run(steiner, sp.SolvingConfig())
