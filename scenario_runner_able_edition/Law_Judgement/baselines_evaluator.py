#!/usr/bin/env python3

import os
import time
import numpy as np
import ujson as json
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error
import scipy.stats as stats
#from sklearn.metrics import PredictionErrorDisplay

from law_judgement_extended import Monitor
from gflownet.generator.generative_model.utils import *
from gflownet.generator.generative_model.dataset import GFNSet
from violation_auditor import load_json_data
from GFN_trainsurrogate_ensemble import get_trainset_parrellel, SurrogateInferer

with open("violation_formulae.json", "r") as file_formulae:
    violations = json.load(file_formulae)
violations_list = list(violations.keys())

def get_robustness_list_with_idx(scenario):
    monitor = Monitor(scenario)
    list_violations = monitor.continuous_monitor_for_violations()
    robustness_list = list(list_violations.values())
    robustness_list[0] = max(robustness_list[1:])
    del monitor
    del list_violations
    idx = int(scenario["ScenarioName"].replace("No_", "").replace("scenario", ""))
    return robustness_list, idx

def calculate_robustness(scenario_dataset):
    scenario_robustness_metalist = [[]] * len(scenario_dataset)
    with ProcessPoolExecutor(max_workers=24) as executor:
        for robustness_list, idx in executor.map(get_robustness_list_with_idx, scenario_dataset):
            scenario_robustness_metalist[idx] = robustness_list
    return scenario_robustness_metalist

def analyze_robustness():
    gflownet_set_dict = {}

    # Training data
    print("Evaluate surrogate model on training dataset:")
    mutated_dir = "traceset_mutated/"

    for session in sorted(os.listdir(mutated_dir)):
        dataset = get_trainset_parrellel(mutated_dir + session + "/")
        gflownet_set = GFNSet(dataset, train=False, g_flag=True)
        gflownet_set_dict[session] = gflownet_set

        actionindexseq_list = []
        groundtruth_robustness_dict = {}
        surrogate_robustness_dict = {}
        violations_eval_dict = {}
        for violation in violations_list:
            violations_eval_dict[violation] = {}
            groundtruth_robustness_dict[violation] = []
            surrogate_robustness_dict[violation] = []

        # Ground truth
        for scenario in dataset:
            for robustness_idx, robustness in enumerate(scenario["robustness"]):
                groundtruth_robustness_dict[violations_list[robustness_idx]].append(robustness)

            actionindexseq = []
            for action in scenario["actions"]:
                actionindexseq.append(gflownet_set.actions_to_index[action])
            actionindexseq_list.append(actionindexseq)
        del dataset

        # Surrogate
        surrogate_robustness_dict[violations_list[0]] = [float("-inf")] * len(actionindexseq_list)
        proxy_model = SurrogateInferer(session)
        robustness_metalist = proxy_model.infer_surrogate_fragment(actionindexseq_list)
        del proxy_model
        for formulae_idx, robustness_list in enumerate(robustness_metalist):
            surrogate_robustness_dict[violations_list[formulae_idx+1]].extend(robustness_list)

            for robustness_idx, robustness in enumerate(robustness_list):
                surrogate_robustness_dict[violations_list[0]][robustness_idx] = max(robustness, surrogate_robustness_dict[violations_list[0]][robustness_idx])

        # Evaluation
        violations_eval_list1 = []
        violations_eval_list2 = []
        violations_eval_list3 = []
        violations_eval_list4 = []
        for violation in violations_eval_dict:
            groundtruth_robustness_array = np.array(groundtruth_robustness_dict[violation])
            surrogate_robustness_array = np.array(surrogate_robustness_dict[violation])
            violations_eval_dict[violation]["MAE"] = mean_absolute_error(groundtruth_robustness_array, surrogate_robustness_array)
            violations_eval_dict[violation]["VAR_groundtruth"] = np.var(groundtruth_robustness_array)
            violations_eval_dict[violation]["VAR_surrogate"] = np.var(surrogate_robustness_array)
            violations_eval_dict[violation]["VAR_res"] = np.var(groundtruth_robustness_array - surrogate_robustness_array)
            """
            print(violation)
            print("MAE:", violations_eval_dict[violation]["MAE"])
            print("Variance of ground truth:", violations_eval_dict[violation]["VAR_groundtruth"])
            print("Variance of surrogate:", violations_eval_dict[violation]["VAR_surrogate"])
            print("Variance of residuel:", violations_eval_dict[violation]["VAR_res"])
            """
            violations_eval_list1.append(np.round(violations_eval_dict[violation]["MAE"], decimals=3).item())
            violations_eval_list2.append(np.round(violations_eval_dict[violation]["VAR_groundtruth"], decimals=3).item())
            violations_eval_list3.append(np.round(violations_eval_dict[violation]["VAR_surrogate"], decimals=3).item())
            violations_eval_list4.append(np.round(violations_eval_dict[violation]["VAR_res"], decimals=3).item())
            #print()
        print("MAE:", violations_eval_list1)
        print("Variance of ground truth:", violations_eval_list2)
        print("Variance of surrogate:", violations_eval_list3)
        print("Variance of residuel:", violations_eval_list4)

        time.sleep(10)

    print("=" * 40)

    # GFlowNet Data
    print("Evaluate surrogate model on GFlowNet data:")
    HOME = os.environ["HOME"]
    trace_dir = HOME + "/scenario_runner_able_edition/trace/"
    for session_dir in sorted(os.listdir(trace_dir)):
        if "bysopt" in session_dir or "rl" in session_dir:
            continue
        if not os.path.isdir(trace_dir + session_dir):
            continue
        session = "_".join(session_dir.split("_")[:2])

        groundtruth_robustness_dict = {}
        surrogate_robustness_dict = {}
        violations_eval_dict = {}
        for violation in violations_list:
            violations_eval_dict[violation] = {}
            groundtruth_robustness_dict[violation] = []
            surrogate_robustness_dict[violation] = []

        # Ground truth
        trace_session_dir = os.path.join(trace_dir, session_dir)
        scenario_List = []
        with ProcessPoolExecutor(max_workers=24) as executor:
            for scenario_data in executor.map(load_json_data, [os.path.join(trace_session_dir, scenario_file) for scenario_file in os.listdir(trace_session_dir)]):
                if scenario_data["weather"]["rain"] >= 1.0:
                    scenario_data["weather"]["rain"] /= 100.0
                if scenario_data["weather"]["sunny"] >= 1.0:
                    scenario_data["weather"]["sunny"] /= 100.0
                if scenario_data["weather"]["wetness"] >= 1.0:
                    scenario_data["weather"]["wetness"] /= 100.0
                if scenario_data["weather"]["fog"] >= 1.0:
                    scenario_data["weather"]["fog"] /= 100.0
                scenario_List.append(scenario_data)

        scenario_robustness_metalist = calculate_robustness(scenario_List)
        for robustness_list in scenario_robustness_metalist:
            for robustness_idx, robustness in enumerate(robustness_list):
                groundtruth_robustness_dict[violations_list[robustness_idx]].append(robustness)

        # Surrogate
        gflownet_set = gflownet_set_dict[session]

        actionseq_path = "generated_actionseq/" + session + "_mk2.json"
        if os.path.isfile(actionseq_path):
            with open(actionseq_path) as actionseq_file:
                generated_actionseq = json.load(actionseq_file)

            actionseq_list = []
            for actionseq_dict in generated_actionseq:
                actionseq = []
                for action in actionseq_dict["actions"]:
                    actionseq.append(gflownet_set.actions_to_index[action])
                actionseq_list.append(actionseq)
        else:
            print(actionseq_path, " not exists.")
            continue

        surrogate_robustness_dict[violations_list[0]] = [float("-inf")] * len(actionseq_list)
        proxy_model = SurrogateInferer(session)
        robustness_metalist = proxy_model.infer_surrogate_fragment(actionseq_list)
        del proxy_model
        for formulae_idx, robustness_list in enumerate(robustness_metalist):
            surrogate_robustness_dict[violations_list[formulae_idx+1]].extend(robustness_list)

            for robustness_idx, robustness in enumerate(robustness_list):
                surrogate_robustness_dict[violations_list[0]][robustness_idx] = max(robustness, surrogate_robustness_dict[violations_list[0]][robustness_idx])

        # Evaluation
        violations_eval_list1 = []
        violations_eval_list2 = []
        violations_eval_list3 = []
        violations_eval_list4 = []
        for violation in violations_eval_dict:
            groundtruth_robustness_array = np.array(groundtruth_robustness_dict[violation])
            surrogate_robustness_array = np.array(surrogate_robustness_dict[violation])
            violations_eval_dict[violation]["MAE"] = mean_absolute_error(groundtruth_robustness_array, surrogate_robustness_array)
            violations_eval_dict[violation]["VAR_groundtruth"] = np.var(groundtruth_robustness_array)
            violations_eval_dict[violation]["VAR_surrogate"] = np.var(surrogate_robustness_array)
            violations_eval_dict[violation]["VAR_res"] = np.var(groundtruth_robustness_array - surrogate_robustness_array)
            """
            print(violation)
            print("MAE:", violations_eval_dict[violation]["MAE"])
            print("Variance of ground truth:", violations_eval_dict[violation]["VAR_groundtruth"])
            print("Variance of surrogate:", violations_eval_dict[violation]["VAR_surrogate"])
            print("Variance of residuel:", violations_eval_dict[violation]["VAR_res"])
            """
            violations_eval_list1.append(np.round(violations_eval_dict[violation]["MAE"], decimals=3).item())
            violations_eval_list2.append(np.round(violations_eval_dict[violation]["VAR_groundtruth"], decimals=3).item())
            violations_eval_list3.append(np.round(violations_eval_dict[violation]["VAR_surrogate"], decimals=3).item())
            violations_eval_list4.append(np.round(violations_eval_dict[violation]["VAR_res"], decimals=3).item())
            #print()
        print("MAE:", violations_eval_list1)
        print("Variance of ground truth:", violations_eval_list2)
        print("Variance of surrogate:", violations_eval_list3)
        print("Variance of residuel:", violations_eval_list4)

        time.sleep(10)

if __name__ == '__main__':
    analyze_robustness()
