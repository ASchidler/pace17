from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

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
        component.ComponentReduction(),
        degree.DegreeReduction(),
        bound_reductions.BoundNodeReduction(),
        bound_reductions.BoundEdgeReduction(),
        bound_reductions.BoundGraphReduction(),
        bound_reductions.BoundNtdkReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        degree.DegreeReduction(),
        dual_ascent.DualAscent(quick_run=True),
        component.ComponentReduction(),
        # Last test so the bound can be used for the solver
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
            # tsp_heuristic.TspHeuristic(steiner),
            #bnd_heuristic.BoundHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
