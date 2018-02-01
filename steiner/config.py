from solver import solver_2k as sv
from reduction import *
from preselection import *


def reducers():
    return [
        component.ComponentReduction(),
        zeroedge.ZeroEdgeReduction(),
        # short_edges.ShortEdgeReduction(),
        degree.DegreeReduction(),
        incidence.IncidenceReduction(),
        voronoi.VoronoiReduction(),
        terminal_distance.TerminalDistanceReduction(),
        long_edges.LongEdgeReduction(),
        ntdk.NtdkReduction(),
        reachability.ReachabilityReduction(),
        cut_reachability.CutReachabilityReduction(),
        terminals.TerminalReduction()
    ]


def solver(steiner):
    return sv.Solver2k(steiner)
