import os
import sys
from collections import defaultdict
import re
import pandas as pd
import matplotlib.pyplot as plt


class InstanceResult:
    """Represents the result of one instance run"""
    def __init__(self):
        # General info, name of the instance, run ID, time, memory und time for reductions
        self.name = None
        self.run = None
        self.runtime = 0
        self.memory = 0
        self.reduce_time = 0

        # vertex, edge, terminal count pre and post preprocessing. Only available for TU solver
        self.v_start = -1
        self.e_start = -1
        self.t_start = -1
        self.v_run = -1
        self.e_run = -1
        self.t_run = -1

        # Result. Does the error file contain st? Out of memory, out of time, solved and what was the result?
        self.error = False
        self.mem_out = False
        self.time_out = False
        self.solved = False
        self.result = -1

        # Aggregation result. Divergence of numbers
        self.memory_div = 0
        self.runtime_div = 0


class OverallStatistic:
    def __init__(self):
        self.solved = 0
        self.not_solved = 0
        self.runtime = 0
        self.memory = 0
        self.runtime_div = 0
        self.memory_div = 0
        self.memory_out = 0
        self.runtime_out = 0

def parse_watcher(path, instance):
    """Parses the condor watcher file"""
    f = open(path, "r")

    for line in f:
        if line.startswith("Real time"):
            instance.runtime = float(line.split(":").pop())
        elif line.startswith("Max. virtual"):
            instance.memory = int(line.split(":").pop())
        elif line.startswith("Maximum VSize exceeded"):
            instance.mem_out = True
        elif line.startswith("Maximum wall clock time exceeded"):
            instance.mem_out = True


def parse_log(path, instance):
    """Parses the log file. Depending on the solver there may be more or less information"""
    f = open(path, "r")
    is_tu = None

    def parse_counts(l):
        m = re.search("([0-9]+) vertices.*?([0-9]+) edges.*?([0-9]+) terminals", l)
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    for line in f:
        if is_tu is None:
            if line.startswith("VALUE"):
                instance.result = int(line.strip().split(" ").pop())
                instance.solved = True
                break
            else:
                is_tu = True
        if is_tu:
            if line.startswith("Loaded"):
                instance.v_start, instance.e_start, instance.t_start = parse_counts(line)
            elif line.startswith("Solving"):
                instance.v_run, instance.e_run, instance.t_run = parse_counts(line)
            elif line.startswith("Reductions completed"):
                instance.reduce_time = float(line.split(" ").pop())
            elif line.startswith("Final solution"):
                instance.solved = True
                instance.result = int(line.split(":").pop())


def parse_error(path, instance):
    """Parses the error file"""
    instance.error = os.stat(path).st_size > 0


def aggregate_instance(instances):
    """Multiple runs cause multiple data for an instance to exist. This function aggregates it to one dataset"""
    cnt = 0
    new_instance = InstanceResult()
    new_instance.run = "All"
    mem_out = False
    time_out = False
    error = False
    solved = False

    for inst in instances:
        new_instance.name = inst.name

        solved |= inst.solved
        mem_out |= inst.mem_out
        time_out |= inst.time_out
        error |= inst.error

        if inst.solved:
            cnt += 1
            new_instance.solved = True
            new_instance.result = inst.result
            new_instance.v_run, new_instance.e_run, new_instance.t_run = inst.v_run, inst.e_run, inst.t_run
            new_instance.v_start, new_instance.e_start, new_instance.t_start = inst.v_start, inst.e_start, inst.t_start
            new_instance.memory += inst.memory
            new_instance.reduce_time += inst.reduce_time
            new_instance.runtime += inst.runtime

    if cnt > 0:
        new_instance.memory /= cnt
        new_instance.reduce_time /= cnt
        new_instance.runtime /= cnt
        for inst in instances:
            if inst.solved:
                new_instance.runtime_div += abs(new_instance.runtime - inst.runtime)
                new_instance.memory_div += abs(new_instance.memory_div - inst.memory)
    else:
        new_instance.time_out = time_out
        new_instance.mem_out = mem_out
        new_instance.error = error

    return new_instance


def parse_run(base_path):
    results = defaultdict(lambda: defaultdict(lambda: InstanceResult()))

    for subdir, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".watcher"):
                # Run ID is the last directory of the path
                _, run_no = os.path.split(subdir)

                # Get the instance name by stripping the .watcher extension
                parts = f.split(".")
                parts.pop()
                instance_name = ".".join(parts)

                # Set basic information
                instance = results[instance_name][run_no]
                instance.name = instance_name
                instance.run = run_no

                # Parse watcher file
                parse_watcher(os.path.join(subdir, f), instance)
                parse_log(os.path.join(subdir, instance_name + ".txt"), instance)
                parse_error(os.path.join(subdir, instance_name + ".err"), instance)

    return results


def calc_statistic(run_data):
    all_stats = dict()
    aggr_results = dict()
    inst_results = defaultdict(list)

    for solver, instances in run_data.items():
        stats = OverallStatistic()
        result_list = []
        for name, runs in instances.items():
            result_list.append(aggregate_instance(runs.values()))
        aggr_results[solver] = result_list

        result_list.sort(key=lambda x: x.name)
        for instance in result_list:
            inst_results[instance.name].append(instance)
            stats.runtime_div += instance.runtime_div
            stats.memory_div += instance.memory_div
            stats.runtime += instance.runtime
            stats.memory += instance.memory

            if instance.solved:
                stats.solved += 1
            else:
                stats.not_solved += 1
                if instance.mem_out:
                    stats.memory_out += 1
                elif instance.time_out:
                    stats.runtime_out += 1

        all_stats[solver] = stats

    return all_stats, aggr_results, inst_results


def parse_benchmark(base_path):
    # Find results folder
    def search_folder(start_path):
        for new_name in os.listdir(start_path):
            new_path = os.path.join(start_path, new_name)
            if os.path.isdir(new_path):
                if new_name == "results":
                    return new_path
                else:
                    sub_res = search_folder(new_path)
                    if sub_res is not None:
                        return sub_res
        return None

    target_path = search_folder(base_path)

    results = dict()

    for benchmark in os.listdir(target_path):
        benchmark_path = os.path.join(target_path, benchmark)
        if os.path.isdir(benchmark_path):
            results[benchmark] = parse_run(benchmark_path)

    all_stats, aggr_results, inst_results = calc_statistic(results)
    benchmarks = aggr_results.keys()
    benchmarks.sort()
    for benchmark in benchmarks:
        stats = all_stats[benchmark]
        print "{}: Completed {}, Not {}, Runtime: {}, Divergence {}".format(benchmark, stats.solved, stats.not_solved,
                                                                            stats.runtime, stats.runtime_div)


def parse_results(base_path, targets):
    results = dict()
    for name in os.listdir(base_path):
        if name in targets:
            full_path = os.path.join(base_path, name)
            if os.path.isdir(full_path):
                results[name] = parse_run(full_path)

    all_stats, aggr_results, _ = calc_statistic(results)

    results = aggr_results.items()
    results.sort()

    frames = []
    names = []

    for solver, instances in results:
        vals = [x.runtime for x in instances if x.solved]
        vals.sort()
        frames += [pd.DataFrame(vals)]
        names.append(solver)
        stats = all_stats[solver]
        print "{}: Completed {}, Not {}, Runtime: {}, Divergence {}".format(solver, stats.solved, stats.not_solved, stats.runtime, stats.runtime_div)

    frame = pd.concat(frames, ignore_index=True, axis = 1)
    frame.cumsum()
    ax = frame.plot(style=['bs-', 'ro-', 'y^-', 'g*-'])
    ax.legend(names)

    axes = plt.axes()
    axes.set_xlabel("instances")
    axes.set_ylabel("time (s)")
    axes.set_xlim(100, 200)

    plt.show()




pth = sys.argv[1]
trg = {sys.argv[i] for i in range(2, len(sys.argv))}

if len(trg) == 1:
    parse_benchmark(os.path.join(pth, trg.pop()))
else:
    parse_results(sys.argv[1], trg)
