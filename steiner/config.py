from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""

def reducers():
    """Creates the set of reducing preprocessing tests"""
    return [
        terminal_distance.CostVsTerminalDistanceReduction(),
        long_edges.LongEdgeReduction(),
        degree.DegreeReduction(),
        voronoi.VoronoiReduction(),
        ntdk.NtdkReduction(),
        terminals.TerminalReduction(),
        short_edges.ShortEdgeReduction(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        reachability.ReachabilityReduction(),
    ]


def once_reducers():
    """Creates the set of reductions/inclusions that should/need not be run more than once"""
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction()
    ]

def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            #tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
