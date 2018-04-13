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
        ntdk.NtdkReduction(True),
        sdc.SdcReduction(),
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        component.ComponentReduction(),
        ntdk.NtdkReduction(False),
        #nearest_vertex.NearestVertex(),
        #short_links.ShortLinkPreselection(),
        #degree.DegreeReduction(),
        #terminals.TerminalReduction(),
        preselection_pack.NvSlPack(),
        # voronoi_nodes.VoronoiNodeReduction(),
        # voronoi.VoronoiReduction(),
        # bound_reductions.BoundNodeReduction(),
        # bound_reductions.BoundEdgeReduction(),
        # bound_reductions.BoundGraphReduction(),
        # bound_reductions.BoundNtdkReduction(),
        dual_ascent.DualAscent(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        terminals.TerminalReduction(),
        component.ComponentReduction(),
        # cut_reachability.CutReachabilityReduction(),
        # cut_reachability_edge.CutReachabilityEdgeReduction(),
        # reachability.ReachabilityReduction(),
    ]


def contractors():
    return [
        #terminals.TerminalReduction(),
        #nearest_vertex.NearestVertex(),
        #short_links.ShortLinkPreselection(),
        terminal_distance.CostVsTerminalDistanceReduction()
    ]


def solver(steiner):
    """Creates a solver"""
    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            # smt_heuristic.SmtHeuristic(steiner, 3),
            # tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
