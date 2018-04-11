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
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        component.ComponentReduction(),
        long_edges.LongEdgeReduction(False),
        sdc.SdcReduction(),
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        component.ComponentReduction(),
        degree.DegreeReduction(),
        # voronoi_nodes.VoronoiNodeReduction(),
        # voronoi.VoronoiReduction(),
        bound_reductions.BoundNodeReduction(),
        bound_reductions.BoundEdgeReduction(),
        bound_reductions.BoundGraphReduction(),
        bound_reductions.BoundNtdkReduction(),
        ntdk.NtdkReduction(False),
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        component.ComponentReduction(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        reachability.ReachabilityReduction(),
        long_edges.LongEdgeReduction(True)
    ]


def contractors():
    return [
        #terminals.TerminalReduction(),
        nearest_vertex.NearestVertex(),
        short_links.ShortLinkPreselection(),
    ]


def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            # smt_heuristic.SmtHeuristic(steiner, 3),
            # tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
