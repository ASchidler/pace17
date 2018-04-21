from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *
import solver.heuristics.da_heuristic as da

"""Used as a configuration for the whole steiner solving suite"""


def reducers():
    """Creates the set of reducing preprocessing tests"""
    return [
        dual_ascent.DualAscent(run_once=True),
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        degree.DegreeReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        long_edges.LongEdgeReduction(True),
        ntdk.NtdkReduction(True),
        sdc.SdcReduction(),
        degree.DegreeReduction(),
        ntdk.NtdkReduction(False),
        degree.DegreeReduction(),
        ntdk.NtdkReduction(False, search_limit=100, only_last=True),
        degree.DegreeReduction(),
        preselection_pack.NvSlPack(),
        dual_ascent.DualAscent(),
        dual_ascent.DualAscent(quick_run=True, start_at=3),
        component.ComponentReduction(),
        degree.DegreeReduction(),
        bound_reductions.BoundNodeReduction(),
        bound_reductions.BoundEdgeReduction(),
        bound_reductions.BoundGraphReduction(),
        bound_reductions.BoundNtdkReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction()
    ]

def solver(steiner):
    """Creates a solver"""
    heuristics = [mst_heuristic.MstHeuristic(steiner)]
    da_h = da.DaHeuristic(steiner)
    #heuristics.append(da_h)
    slv = sv.Solver2k(steiner, steiner.terminals, heuristics)
    da_h.solver = slv
    return slv
