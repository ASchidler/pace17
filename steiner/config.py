from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *
import solver.heuristics.da_heuristic as da

"""Used as a configuration for the whole steiner solving suite"""

# TODO: B&B implementation branching on node of highest degree in best solution with reductions
def reducers():
    """Creates the set of reducing preprocessing tests"""
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        #dual_ascent.DualAscent(run_once=True, run_last=False),
        component.ComponentReduction(),
        degree.DegreeReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        long_edges.LongEdgeReduction(True),
        ntdk.NtdkReduction(True),
        sdc.SdcReduction(),
        degree.DegreeReduction(),
        ntdk.NtdkReduction(False),
        degree.DegreeReduction(),
        preselection_pack.NvSlPack(),
        dual_ascent.DualAscent(start_at=1, run_every=2, run_last=True),
        component.ComponentReduction(),
        degree.DegreeReduction(),
        bound_reductions.BoundNodeReduction(start_at=2),
        bound_reductions.BoundEdgeReduction(start_at=2),
        bound_reductions.BoundGraphReduction(start_at=2),
        bound_reductions.BoundNtdkReduction(start_at=2),
        terminal_distance.CostVsTerminalDistanceReduction(),
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
