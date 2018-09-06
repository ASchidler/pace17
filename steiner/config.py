from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""


def reducers(exclude_reduction=False):
    """Creates the set of reducing preprocessing tests"""
    red = [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        component.ComponentReduction(),
        #heavy_edge.HeavyEdge(),
        degree.DegreeReduction(),
        mst_contract.MstContract(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        long_edges.LongEdgeReduction(True),
        ntdk.NtdkReduction(True, max_degree=4),
        sdc.SdcReduction(),
        deg3.Degree3Reduction(),
        degree.DegreeReduction(),
        ntdk.NtdkReduction(False, max_degree=4),
        degree.DegreeReduction(),
        #short_edges.ShortEdgeReduction(),
        preselection_pack.NvSlPack(),
        degree.DegreeReduction(),
        #bound_reductions.BoundNodeReduction(),
        #bound_reductions.BoundEdgeReduction(),
        #bound_reductions.BoundGraphReduction(),
        #bound_reductions.BoundNtdkReduction(),
        dual_ascent.DualAscent(),
        component.ComponentReduction(),
        degree.DegreeReduction()
    ]

    # This is to allow for removing reductions taken from other PACE submissions
    if exclude_reduction:
        red.pop(11)     # Degree 3
        red.pop(5)      # MST contract
        red.pop(3)      # Heavy edge

    return red

def solver(steiner):
    """Creates a solver"""
    da_h = da_heuristic.DaHeuristic(steiner)

    if len(steiner.graph.nodes) < 2000 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 3:
        heuristics = [da_h]
    else:
        heuristics = [mst_heuristic.MstHeuristic(steiner)]

    slv = sv.Solver2k(steiner, steiner.terminals, heuristics)
    da_h.solver = slv
    return slv
