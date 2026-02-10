#!/usr/bin/env python3

import os
import json
import random
import numpy as np
from law_judgement_extended import Monitor
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt

VIOLATION_CLAUSES_TOTAL_AMOUNT = 81

def load_json_data(file_name):
    with open(file_name, 'r') as trace_file:
        data = json.load(trace_file)
    if isinstance(data, dict) and data["ScenarioName"] == "scenario0":
        idx = os.path.splitext(file_name)[0].split("_")[-1]
        data["ScenarioName"] = "scenario" + idx
    return data

def load_json_data_with_idx(file_name):
    with open(file_name, 'r') as trace_file:
        data = json.load(trace_file)
    if isinstance(data, dict) and data["ScenarioName"] == "scenario0":
        idx = os.path.splitext(file_name)[0].split("_")[-1]
        data["ScenarioName"] = "scenario" + idx
    return data, int(idx)

def get_robustness(scenario):
    monitor = Monitor(scenario)
    list_violations = monitor.continuous_monitor_for_violations()
    violations_dict = {}
    for violation in list(list_violations.keys())[1:]:
        if list_violations[violation] >= 0.:
            violations_dict[violation] = list_violations[violation]
    del monitor
    del list_violations
    return violations_dict

def get_robustness_with_idx(scenario):
    monitor = Monitor(scenario)
    list_violations = monitor.continuous_monitor_for_violations()
    violations_dict = {}
    for violation in list(list_violations.keys())[1:]:
        if list_violations[violation] >= 0.:
            violations_dict[violation] = list_violations[violation]
    del monitor
    del list_violations
    idx = int(scenario["ScenarioName"].replace("No_", "").replace("scenario", ""))
    return violations_dict, idx

def get_violations_dict_list(scenario_dataset):
    violations_dict_list = [{}] * len(scenario_dataset)
    with ProcessPoolExecutor(max_workers=24) as executor:
        for violations_dict, idx in executor.map(get_robustness_with_idx, scenario_dataset):
            violations_dict_list[idx] = violations_dict
    return violations_dict_list

def get_total_clauses(scenario_dataset):
    violations_dict_list = get_violations_dict_list(scenario_dataset)
    violations_dict_accumulation = {}

    for violations_dict in violations_dict_list:
        violations_dict_accumulation.update(violations_dict)

    return violations_dict_accumulation

def get_stats_incremental_clauses(scenario_dataset):
    violations_dict_list = get_violations_dict_list(scenario_dataset)
    violations_dict_accumulation = {}
    violations_increment_counter = [0]

    for violations_dict in violations_dict_list:
        violations_dict_accumulation.update(violations_dict)
        violations_increment_counter.append(len(violations_dict_accumulation))

    return violations_increment_counter

def get_violation_matrix(scenario_dataset):
    violation_matrix = np.zeros((len(scenario_dataset), VIOLATION_CLAUSES_TOTAL_AMOUNT + 1), dtype=np.int32)

    with ProcessPoolExecutor(max_workers=24) as executor:
        for violations_dict, scenario_idx in executor.map(get_robustness_with_idx, scenario_dataset):
            for violation in list(violations_dict.keys()):
                violation_idx = int(violation.replace("sub_law_violation_", ""))
                violation_matrix[scenario_idx][violation_idx] = 1

    return violation_matrix

def plot_bar_method_comparison(violation_matrix_dict):
    method_label = {
        "rs": "Random Search",
        "ga": "Genetic Algorithm",
        "bysopt": "Bayesian Optimization",
        "rl": "Deep Q Network",
        "mk2": "GFlowNet",
    }

    hatch = {
        "rs": "",
        "ga": "..",
        "bysopt": "//",
        "rl": "\\",
        "mk2": "++",
    }

    # Create matrix with violation formulae quantile
    violation_matrix_dict_quantile_99 = {}
    for method in violation_matrix_dict:
        violation_matrix = np.copy(violation_matrix_dict[method])
        formulae_mask_array = np.where(violation_matrix.sum(axis=0) < violation_matrix.shape[0] * .99, 1, 0)
        violation_matrix = violation_matrix * formulae_mask_array
        violation_matrix_dict_quantile_99[method] = violation_matrix

    x = np.arange(2)
    width = 0.15
    fig, ax = plt.subplots(2, 1, figsize=(8, 4), sharex=True)

    # Violating scenario quantity
    multiplier = -1
    for method in violation_matrix_dict:
        offset = width * multiplier
        scenario_violating_array1 = violation_matrix_dict[method].sum(axis=1)
        scenario_violating_array2 = violation_matrix_dict_quantile_99[method].sum(axis=1)
        violating_scenario_quantity_list = [
            np.count_nonzero(scenario_violating_array1),
            np.count_nonzero(scenario_violating_array2)
        ]
        rects = ax[0].bar(x + offset,
                          violating_scenario_quantity_list,
                          edgecolor='black',
                          hatch=hatch[method],
                          width=width,
                          label=method_label[method])
        ax[0].bar_label(rects, padding=1.0)
        multiplier += 1
    ax[0].set_title("Comparison of effectiveness", pad=4.0)
    ax[0].set_xticks(x + width, ("100%", "<99%"))
    ax[0].set_ylabel("#Violating Senarios")
    ax[0].set_ylim(ymin=0, ymax=600)

    # Violation formulae variants
    multiplier = -1
    for method in violation_matrix_dict:
        offset = width * multiplier
        violation_formulae_array1 = violation_matrix_dict[method].sum(axis=0)
        violation_formulae_array2 = violation_matrix_dict_quantile_99[method].sum(axis=0)
        violation_formulae_variants_list = [
            np.count_nonzero(violation_formulae_array1),
            np.count_nonzero(violation_formulae_array2)
        ]
        rects = ax[1].bar(x + offset,
                          violation_formulae_variants_list,
                          edgecolor='black',
                          hatch=hatch[method],
                          width=width,
                          label=method_label[method])
        ax[1].bar_label(rects, padding=1.0)
        multiplier += 1
    ax[1].set_title("Comparison of diversity", pad=4.0)
    ax[1].set_xticks(x + width, ("100%", "<99%"))
    ax[1].set_ylabel("#Covered Violation Formulae")
    ax[1].set_ylim(ymin=0, ymax=30)

    fig.tight_layout(pad=2.0)

    plt.subplots_adjust(right=0.7)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 2.5))

    save_path = "result_images/"
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    plt.savefig(save_path + "bar_methods_comparison.png", dpi=300)

"""
def plot_step_figure(gfn_tuple_list, ga_tuple_list, ads):
    fontsize = 12
    fig, ax = plt.subplots(1, len(gfn_tuple_list), figsize=(12, 3.5), sharex=True, sharey=True)
    for session_idx in range(len(gfn_tuple_list)):
        ax[session_idx].step(gfn_tuple_list[session_idx][0], gfn_tuple_list[session_idx][1], where='post', label="GFlowNet")
        ax[session_idx].step(ga_tuple_list[session_idx][0], ga_tuple_list[session_idx][1], where='post', label="Genetic Algorithm")
        #ax[session_idx].set_xlim(xmin=0, xmax=512)
        ax[session_idx].set_xticks(range(0, 512, 200), fontsize=fontsize)
        ax[session_idx].set_xlabel("#Testing Scenarios", fontsize=fontsize)
        ax[session_idx].set_ylim(ymax=32)
        ax[session_idx].set_yticks(range(0, 31, 10), fontsize=fontsize)
        ax[session_idx].set_axisbelow(True)
        ax[session_idx].spines['right'].set_visible(False)
        ax[session_idx].spines['top'].set_visible(False)
        ax[session_idx].set_title("Session = S" + str(session_idx + 1))
    ax[0].set_ylabel("#Violation Formulae", fontsize=fontsize)
    ax[-1].legend(loc="upper right")
    plt.tight_layout()
    #fig.suptitle("Comparison of GFN and GA")
    #plt.show()

    save_path = "results_step/"
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    plt.savefig(save_path + ads + ".png", dpi=300)
"""

def plot_step_figure(gfn_tuple_dict):
    fontsize = 12
    for ads in gfn_tuple_dict:
        session_count = len(gfn_tuple_dict[ads])
    fig, ax = plt.subplots(1, session_count, figsize=(12, 3.5), sharex=True, sharey=True)
    for session_idx in range(session_count):
        for ads in gfn_tuple_dict:
            ax[session_idx].step(gfn_tuple_dict[ads][session_idx][0], gfn_tuple_dict[ads][session_idx][1], where='post', label=ads.replace("_", "").title())
        #ax[session_idx].set_xlim(xmin=0, xmax=512)
        ax[session_idx].set_xticks(range(0, 512, 200), fontsize=fontsize)
        ax[session_idx].set_xlabel("#Testing Scenarios", fontsize=fontsize)
        ax[session_idx].set_ylim(ymax=32)
        ax[session_idx].set_yticks(range(0, 31, 10), fontsize=fontsize)
        ax[session_idx].set_axisbelow(True)
        ax[session_idx].spines['right'].set_visible(False)
        ax[session_idx].spines['top'].set_visible(False)
        ax[session_idx].set_title("Session = S" + str(session_idx + 1))
    ax[0].set_ylabel("#Violation Formulae", fontsize=fontsize)
    ax[-1].legend(loc="best")
    plt.tight_layout()
    #fig.suptitle("Comparison of GFN and GA")
    #plt.show()

    save_path = "results_step/"
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    plt.savefig(save_path + "all_ads.png", dpi=300)

def make_step_plot(analysis_dir = "analysis_traceset/"):
    ignore_weather = True

    # GA
    """
    mutated_dir = "traceset_mutated/"
    ga_tuple_list = []
    ga_tuple_metalist = []
    for session in sorted(os.listdir(mutated_dir)):
        ga_tuple_sublist = []
        if not os.path.isdir(mutated_dir + session):
            continue
        for subsession in os.listdir(mutated_dir + session):
            cache_path = analysis_dir + subsession.replace("mutated_traceset", "cache")
            if os.path.isfile(cache_path):
                with open(cache_path, 'r') as cache_file:
                    ga_tuple = json.load(cache_file)
            else:
                data = load_json_data(mutated_dir + session + "/" + subsession)
                for scenario_data in data:
                    if ignore_weather:
                        scenario_data["weather"]["rain"] = 0
                        scenario_data["weather"]["sunny"] = 0
                        scenario_data["weather"]["wetness"] = 0
                        scenario_data["weather"]["fog"] = 0
                    else:
                        if scenario_data["weather"]["rain"] >= 1.0:
                            scenario_data["weather"]["rain"] /= 100.0
                        if scenario_data["weather"]["sunny"] >= 1.0:
                            scenario_data["weather"]["sunny"] /= 100.0
                        if scenario_data["weather"]["wetness"] >= 1.0:
                            scenario_data["weather"]["wetness"] /= 100.0
                        if scenario_data["weather"]["fog"] >= 1.0:
                            scenario_data["weather"]["fog"] /= 100.0
                stats_incremental_clauses = get_stats_incremental_clauses(data)
                ga_tuple = (range(len(stats_incremental_clauses)), stats_incremental_clauses)
                with open(cache_path, 'w') as cache_file:
                    json.dump(ga_tuple, cache_file, indent=4)
            ga_tuple_sublist.append(ga_tuple)
        ga_tuple_sublist.sort(key=lambda ga_tuple:ga_tuple[1][-1], reverse=True)
        ga_tuple_sublist = ga_tuple_sublist[:4]
        random.shuffle(ga_tuple_sublist)
        ga_tuple_metalist.append(ga_tuple_sublist)
    while len(ga_tuple_metalist[0]) > 0:
        for ga_tuple_sublist in ga_tuple_metalist:
            ga_tuple_list.append(ga_tuple_sublist.pop(0))
    """

    gfn_tuple_dict = {}
    for ads in ["apollo", "autoware", "interfuser", "behavior_agent"]:
        total_dict = {}
        # GFN
        print(ads)
        gfn_dir = "trace_" + ads + "/"
        gfn_dir_batch_2 = "trace_" + ads + "_batch_2/"
        gfn_tuple_list = []
        gfn_tuple_dict[ads] = []
        for _session in sorted(os.listdir(gfn_dir)):
            session = _session.replace("temp_", "")
            if "half" in session or "quater" in session:
                continue
            print(session)

            # Assemble testing results of generated scenarios
            scenario_List = []
            with ProcessPoolExecutor(max_workers=24) as executor:
                for scenario_data in executor.map(load_json_data, [gfn_dir + _session + "/" + scenario_file for scenario_file in os.listdir(gfn_dir + _session + "/")]):
                    if ignore_weather:
                        scenario_data["weather"]["rain"] = 0.
                        scenario_data["weather"]["sunny"] = 0.
                        scenario_data["weather"]["wetness"] = 0.
                        scenario_data["weather"]["fog"] = 0.
                    else:
                        if scenario_data["weather"]["rain"] >= 1.0:
                            scenario_data["weather"]["rain"] /= 100.0
                        if scenario_data["weather"]["sunny"] >= 1.0:
                            scenario_data["weather"]["sunny"] /= 100.0
                        if scenario_data["weather"]["wetness"] >= 1.0:
                            scenario_data["weather"]["wetness"] /= 100.0
                        if scenario_data["weather"]["fog"] >= 1.0:
                            scenario_data["weather"]["fog"] /= 100.0
                    scenario_List.append(scenario_data)
            batch_1_length = len(scenario_List)
            with ProcessPoolExecutor(max_workers=24) as executor:
                for scenario_data in executor.map(load_json_data, [gfn_dir_batch_2 + _session + "/" + scenario_file for scenario_file in os.listdir(gfn_dir_batch_2 + _session + "/")]):
                    if ignore_weather:
                        scenario_data["weather"]["rain"] = 0.
                        scenario_data["weather"]["sunny"] = 0.
                        scenario_data["weather"]["wetness"] = 0.
                        scenario_data["weather"]["fog"] = 0.
                    else:
                        if scenario_data["weather"]["rain"] >= 1.0:
                            scenario_data["weather"]["rain"] /= 100.0
                        if scenario_data["weather"]["sunny"] >= 1.0:
                            scenario_data["weather"]["sunny"] /= 100.0
                        if scenario_data["weather"]["wetness"] >= 1.0:
                            scenario_data["weather"]["wetness"] /= 100.0
                        if scenario_data["weather"]["fog"] >= 1.0:
                            scenario_data["weather"]["fog"] /= 100.0
                    scenario_data["ScenarioName"] = "scenario" + str(int(scenario_data["ScenarioName"].replace("scenario", "")) + batch_1_length)
                    scenario_List.append(scenario_data)
            stats_incremental_clauses = get_stats_incremental_clauses(scenario_List)
            ga_tuple = (range(len(stats_incremental_clauses)), stats_incremental_clauses)
            gfn_tuple_list.append(ga_tuple)
            gfn_tuple_dict[ads].append(ga_tuple)
            total_dict.update(get_total_clauses(scenario_List))
        print()

        print("total:", len(total_dict))
        print(sorted([int(violation.replace("sub_law_violation_", "")) for violation in total_dict.keys()], key=int))
        print()

        # Compare GFN with GA
        #plot_step_figure(gfn_tuple_list, ga_tuple_list, ads)
        #ga_tuple_list = ga_tuple_list[4:]
    plot_step_figure(gfn_tuple_dict)

def compare_ADS_violation():
    ignore_weather = False

    HOME = os.environ["HOME"]

    violation_frequency_dict = {}
    for ads in ["apollo", "autoware", "interfuser", "behavior_agent"]:
        print("ADS:", ads)

        trace_dir1 = HOME + "/scenario_runner_able_edition/trace_{}/".format(ads)
        trace_dir2 = HOME + "/scenario_runner_able_edition/trace_{}_batch_2/".format(ads)
        scenario_file_list_dict = {}
        for session in sorted(os.listdir(trace_dir1)):
            if "half" in session or "quater" in session:
                continue

            trace_session_dir = os.path.join(trace_dir1, session)
            scenario_file_list_dict[session] = [os.path.join(trace_session_dir, scenario_file) for scenario_file in os.listdir(trace_session_dir)]
            trace_session_dir = os.path.join(trace_dir2, session)
            scenario_file_list_dict[session].extend([os.path.join(trace_session_dir, scenario_file) for scenario_file in os.listdir(trace_session_dir)])

            scenario_List = []
            with ProcessPoolExecutor(max_workers=24) as executor:
                for scenario_data in executor.map(load_json_data, scenario_file_list_dict[session]):
                    if ignore_weather:
                        scenario_data["weather"]["rain"] = .0
                        scenario_data["weather"]["sunny"] = .0
                        scenario_data["weather"]["wetness"] = .0
                        scenario_data["weather"]["fog"] = .0
                    else:
                        if scenario_data["weather"]["rain"] >= 1.0:
                            scenario_data["weather"]["rain"] /= 100.0
                        if scenario_data["weather"]["sunny"] >= 1.0:
                            scenario_data["weather"]["sunny"] /= 100.0
                        if scenario_data["weather"]["wetness"] >= 1.0:
                            scenario_data["weather"]["wetness"] /= 100.0
                        if scenario_data["weather"]["fog"] >= 1.0:
                            scenario_data["weather"]["fog"] /= 100.0
                    scenario_List.append(scenario_data)
            violation_matrix = get_violation_matrix(scenario_List)

            if not ads in violation_frequency_dict:
                violation_frequency_dict[ads] = violation_matrix.sum(axis=0)
            else:
                violation_frequency_dict[ads] = np.add(violation_frequency_dict[ads], violation_matrix.sum(axis=0))

            print("session:", session)
            print("Formulae amounts:", np.count_nonzero(violation_matrix.sum(axis=0)))

        violation_frequency_array = violation_frequency_dict[ads]
        sorted_indices = np.argsort(violation_frequency_array)[::-1]
        sorted_array = violation_frequency_array[sorted_indices]
        print("Formulae amounts:", np.count_nonzero(violation_frequency_array))
        print("Indices:", sorted_indices.tolist())
        print("Scenario amounts:", sorted_array.tolist())
        print()

def create_method_comparison_bar_plot():
    if os.path.isfile("violation_matrix_dict.json"):
        with open("violation_matrix_dict.json", 'r') as violation_matrix_file:
            violation_matrix_dict = json.load(violation_matrix_file)
        for method in violation_matrix_dict:
            violation_matrix_dict[method] = np.array(violation_matrix_dict[method][:512], np.int32)
        plot_bar_method_comparison(violation_matrix_dict)
        return

    ignore_weather = False

    violation_matrix_dict = {}
    violation_matrix_dict["rs"] = None

    mutated_dir = "traceset_mutated/"
    session = sorted(os.listdir(mutated_dir))[0]

    files = []
    path_mutated = mutated_dir + session + "/"
    for traceset_mutated in os.listdir(path_mutated):
        files.append(path_mutated + traceset_mutated)
    dataset = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        for dataset_scenario in executor.map(load_json_data, files):
            dataset.extend(dataset_scenario)

    scenario_List = []
    mutated_traceset_amount = len(os.listdir(path_mutated))
    total_each_traceset = len(dataset) // mutated_traceset_amount
    for mutated_traceset_idx in range(mutated_traceset_amount):
        start_idx = mutated_traceset_idx * total_each_traceset
        end_idx = (mutated_traceset_idx + 1) * total_each_traceset
        scenario_List.extend(dataset[start_idx:end_idx].copy())
    del dataset
    for scenario_data in scenario_List:
        if ignore_weather:
            scenario_data["weather"]["rain"] = .0
            scenario_data["weather"]["sunny"] = .0
            scenario_data["weather"]["wetness"] = .0
            scenario_data["weather"]["fog"] = .0
        else:
            if scenario_data["weather"]["rain"] >= 1.0:
                scenario_data["weather"]["rain"] /= 100.0
            if scenario_data["weather"]["sunny"] >= 1.0:
                scenario_data["weather"]["sunny"] /= 100.0
            if scenario_data["weather"]["wetness"] >= 1.0:
                scenario_data["weather"]["wetness"] /= 100.0
            if scenario_data["weather"]["fog"] >= 1.0:
                scenario_data["weather"]["fog"] /= 100.0
    violation_matrix_dict["ga"] = None
    for mutated_traceset_idx in range(mutated_traceset_amount):
        start_idx = mutated_traceset_idx * total_each_traceset
        end_idx = (mutated_traceset_idx + 1) * total_each_traceset
        scenario_List_fragment = scenario_List[start_idx:end_idx]
        violation_matrix = get_violation_matrix(scenario_List_fragment)
        if violation_matrix_dict["ga"] is None:
            violation_matrix_dict["ga"] = violation_matrix
        else:
            violation_matrix_dict["ga"] = np.concatenate((violation_matrix_dict["ga"], violation_matrix), axis=0)
        del scenario_List_fragment
        del violation_matrix

    HOME = os.environ["HOME"]
    trace_dir = HOME + "/scenario_runner_able_edition/trace/"

    for method_session in os.listdir(trace_dir):
        if not "avunit_s1" in method_session:
            continue
        if not os.path.isdir(trace_dir + method_session):
            continue

        method = method_session.split("_")[-1]

        method_session_dir = trace_dir + method_session + "/"
        scenario_List = []
        with ProcessPoolExecutor(max_workers=24) as executor:
            scenario_file_list = [method_session_dir + scenario_file for scenario_file in os.listdir(method_session_dir)]
            for scenario_data in executor.map(load_json_data, scenario_file_list):
                if ignore_weather:
                    scenario_data["weather"]["rain"] = .0
                    scenario_data["weather"]["sunny"] = .0
                    scenario_data["weather"]["wetness"] = .0
                    scenario_data["weather"]["fog"] = .0
                else:
                    if scenario_data["weather"]["rain"] >= 1.0:
                        scenario_data["weather"]["rain"] /= 100.0
                    if scenario_data["weather"]["sunny"] >= 1.0:
                        scenario_data["weather"]["sunny"] /= 100.0
                    if scenario_data["weather"]["wetness"] >= 1.0:
                        scenario_data["weather"]["wetness"] /= 100.0
                    if scenario_data["weather"]["fog"] >= 1.0:
                        scenario_data["weather"]["fog"] /= 100.0
                scenario_List.append(scenario_data)
        violation_matrix_dict[method] = get_violation_matrix(scenario_List)

    plot_bar_method_comparison(violation_matrix_dict)

    for method in violation_matrix_dict:
        violation_matrix_dict[method] = violation_matrix_dict[method].tolist()
    with open("violation_matrix_dict.json", 'w') as violation_matrix_file:
        json.dump(violation_matrix_dict, violation_matrix_file)

if __name__ == '__main__':
    #create_method_comparison_bar_plot()
    compare_ADS_violation()
