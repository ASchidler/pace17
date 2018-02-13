from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""

def reducers():
    """Creates the set of active reductions/preprocessing"""
    return [
        #component.ComponentReduction(),
        #zeroedge.ZeroEdgeReduction(),
        #incidence.IncidenceReduction(),
        #short_edges.ShortEdgeReduction(),
        degree.DegreeReduction(),
        voronoi.VoronoiReduction(),
        long_edges.LongEdgeReduction(),
        ntdk.NtdkReduction(),
        reachability.ReachabilityReduction(),
        cut_reachability.CutReachabilityReduction(),
        cut_reachability_edge.CutReachabilityEdgeReduction(),
        terminal_distance.CostVsTerminalDistanceReduction(),
        #degree.DegreeReduction(),
        #terminals.TerminalReduction()
    ]


def solver(steiner):
    """Creates a solver"""

    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            #tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
