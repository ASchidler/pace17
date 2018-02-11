from solver import solver_2k as sv
from reduction import *
from preselection import *
from solver.heuristics import *

"""Used as a configuration for the whole steiner solving suite"""

def reducers():
    """Creates the set of active reductions/preprocessing"""
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        incidence.IncidenceReduction(),
        #short_edges.ShortEdgeReduction(),
        degree.DegreeReduction(),
        #voronoi.VoronoiReduction(),
        #ntdk.NtdkReduction(),
        #reachability.ReachabilityReduction(),
        #cut_reachability.CutReachabilityReduction(),
        #cut_reachability_edge.CutReachabilityEdgeReduction(),
        #long_edges.LongEdgeReduction(),
        #terminal_distance.TerminalDistanceReduction(),
        #degree.DegreeReduction(),
        terminals.TerminalReduction()
    ]


def solver(steiner):
    """Creates a solver"""

    heuristics = [
            mst_heuristic.MstHeuristic(steiner),
            tsp_heuristic.TspHeuristic(steiner)
    ]
    return sv.Solver2k(steiner, steiner.terminals, heuristics)
