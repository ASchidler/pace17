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

parser.add_argument('-d', type=int, default=16, help="Width of the d-heap used for solver queue")

parser.add_argument('-b', type=int, default=5000, help="Do not use buckets for small upper bound instances")

parser.add_argument('-a', action='store_false', help="Do not use dual ascent as a guiding heuristic")

parser.add_argument('-t', action='store_false', help="Do not use custom label store")

parser.add_argument('-r', action='store_false', help="Do not use best root from dual ascent")

parser.add_argument('--stats', type=int)

args = parser.parse_args()
f = open(args.filename, "r")
steiner = pp.parse_pace_file(f)

conf = sp.SolvingConfig(debug=True, split=args.s, pace_only=args.p, print_output=True, heavy_edges=args.e,
                        heap_width=args.d, bucket_limit=args.b, use_da=args.a, use_store=args.t, use_root=args.r)

sp.run(steiner, conf)
