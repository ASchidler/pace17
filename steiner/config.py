from solver import solver_2k as sv
from reduction import *
from preselection import *


def reducers():
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
    return sv.Solver2k(steiner, steiner.terminals, True)
