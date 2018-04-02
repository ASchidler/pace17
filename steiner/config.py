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
        bound_reductions.BoundGraphReduction(),
        bound_reductions.BoundNtdkReduction(),
        bound_reductions.BoundNodeReduction(),
        bound_reductions.BoundEdgeReduction(),
        long_edges.LongEdgeReduction(),
        degree.DegreeReduction(),
        voronoi_nodes.VoronoiNodeReduction(),
        voronoi.VoronoiReduction(),
        sdc.SdcReduction(),
        ntdk.NtdkReduction(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        reachability.ReachabilityReduction(),
    ]


def contractors():
    return [
        terminals.TerminalReduction(),
        nearest_vertex.NearestVertex(),
        short_links.ShortLinkPreselection(),
    ]


def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            #smt_heuristic.SmtHeuristic(steiner, 3),
            #tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
