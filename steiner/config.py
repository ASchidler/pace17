from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *
import reduction.two_path as two_path
import reduction.twin_reduction as twin_reduction
import reduction.deg3 as deg3
import solver.heuristics.da_heuristic as da
import reduction.mst_contract as mst_contract
import reduction.heavy_edge as heavy_edge

"""Used as a configuration for the whole steiner solving suite"""

def reducers():
    """Creates the set of reducing preprocessing tests"""
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),

        # dual_ascent.DualAscent(run_once=True, run_last=False),
        component.ComponentReduction(),
        heavy_edge.HeavyEdge(),
        degree.DegreeReduction(),
        #two_path.TwoPath(),
        mst_contract.MstContract(),
        #twin_reduction.TwinReductions(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        long_edges.LongEdgeReduction(True),
        deg3.Degree3Reduction(),
        ntdk.NtdkReduction(True, max_degree=4),
        sdc.SdcReduction(),
        degree.DegreeReduction(),
        ntdk.NtdkReduction(False, max_degree=4),
        degree.DegreeReduction(),
        #short_edges.ShortEdgeReduction(),
        preselection_pack.NvSlPack(),
        degree.DegreeReduction(),
        # bound_reductions.BoundNodeReduction(start_at=2),
        # bound_reductions.BoundEdgeReduction(start_at=2),
        # bound_reductions.BoundGraphReduction(start_at=2),
        # bound_reductions.BoundNtdkReduction(start_at=2),
        dual_ascent.DualAscent(start_at=1, run_every=2, run_last=True),
        component.ComponentReduction(),
        degree.DegreeReduction()
    ]


def solver(steiner):
    """Creates a solver"""
    da_h = da.DaHeuristic(steiner)

    if len(steiner.graph.nodes) < 2500 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 3:
        heuristics = [da_h]
    else:
        heuristics = [mst_heuristic.MstHeuristic(steiner)]

    slv = sv.Solver2k(steiner, steiner.terminals, heuristics)
    da_h.solver = slv
    return slv
