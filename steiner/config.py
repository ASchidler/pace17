from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""

def reducers():
    """Creates the set of reducing preprocessing tests"""
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        long_edges.LongEdgeReduction(),
        degree.DegreeReduction(),
        voronoi.VoronoiReduction(),
        ntdk.NtdkReduction(),
        terminals.TerminalReduction(),
        short_edges.ShortEdgeReduction(),
        short_links.ShortLinkPreselection(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        reachability.ReachabilityReduction(),
    ]


def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            #tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
