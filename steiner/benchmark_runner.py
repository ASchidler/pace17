import sys
import argparse
import iparser as pp
import solving_package as sp

""" This script is used for benchmarking. It offers arguments for configuration"""

parser = argparse.ArgumentParser(description="Steiner tree solver")

parser.add_argument('filename', type=str, help="The filename including path")
parser.add_argument('-s', action='store_true',
                    help="Try to split the graph into smaller sub graphs")

parser.add_argument('-p', action='store_true',
                    help="Use only reductions submitted for PACE")

parser.add_argument('-e', action='store_true', help="Use heavy edges reduction")

parser.add_argument('--stats', type=int)

args = parser.parse_args()
f = open(args.filename, "r")
steiner = pp.parse_pace_file(f)

sp.run(steiner, debug=True, solve=True, reductions=True, verify=False, split=args.s, pace_only=args.p, prnt=True, hvy=args.e)
