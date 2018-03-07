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
        # long_edges.LongEdgeReduction(),
        degree.DegreeReduction(),
        voronoi_nodes.VoronoiNodeReduction(),
        voronoi.VoronoiReduction(),
        ntdk.NtdkReduction(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        reachability.ReachabilityReduction(),
    ]


def contractors():
    return [
        terminals.TerminalReduction(),
        short_edges.ShortEdgeReduction(),
        # length_transform.LengthTransformReduction(),
        # short_links.ShortLinkPreselection(),
    ]


def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            #smt_heuristic.SmtHeuristic(steiner, 3),
            #tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
