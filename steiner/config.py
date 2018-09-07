from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""


def reducers(exclude_new_reduction=False, heavy_edges=True):
    """Creates the set of reducing preprocessing tests"""
    red = [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        component.ComponentReduction(),
        degree.DegreeReduction(contract_first=False),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(contract_first=False),
        long_edges.LongEdgeReduction(True),
        ntdk.NtdkReduction(True, max_degree=4),
        sdc.SdcReduction(),
        deg3.Degree3Reduction(enabled=not exclude_new_reduction),
        degree.DegreeReduction(contract_first=False),
        ntdk.NtdkReduction(False, max_degree=4),
        degree.DegreeReduction(contract_first=False),
        dual_ascent.DualAscent(),
        component.ComponentReduction(),
        degree.DegreeReduction(),
        heavy_edge.HeavyEdge(enabled=heavy_edges),
        # short_edges.ShortEdgeReduction(),
        mst_contract.MstContract(enabled=not exclude_new_reduction),
        preselection_pack.NvSlPack(),
        degree.DegreeReduction(),
        # bound_reductions.BoundNodeReduction(),
        # bound_reductions.BoundEdgeReduction(),
        # bound_reductions.BoundGraphReduction(),
        # bound_reductions.BoundNtdkReduction(),
    ]

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
