#!/usr/bin/env python

import os
import gc
import ujson as json
from concurrent.futures import ProcessPoolExecutor
import subprocess

from law_judgement_extended import Monitor
from GFN_trainsurrogate_ensemble import get_trainset_parrellel, train_surrogate_ensemble
from GFN_traingenerator import generate_one_scenario

def load_and_process_active_learning_data(trace_file_path):
    trace_idx = int(os.path.splitext(trace_file_path)[0].split("_")[-1])

    with open(trace_file_path, 'r') as trace_file:
        trace_data = json.load(trace_file)

    monitor = Monitor(trace_data)
    list_violations = monitor.continuous_monitor_for_violations()
    list_reward = list(list_violations.values())
    list_reward[0] = max(list_reward[1:])

    return list_reward, trace_idx

def get_active_learning_trainset_parrellel(session):
    HOME = os.environ["HOME"]
    SRUNNER_ROOT = HOME + "/scenario_runner_able_edition/"
    trace_dir = SRUNNER_ROOT + "trace/" + session + "_mk2/"
    if not os.path.isdir(trace_dir):
        os.mkdir(trace_dir)
    trace_file_paths = []
    for trace_file in os.listdir(trace_dir):
        trace_file_paths.append(trace_dir + trace_file)

    generated_scenarios_path = "generated_scenarios/" + session + "_mk2.json"
    if os.path.isfile(generated_scenarios_path):
        with open(generated_scenarios_path, 'r') as scenarios_file:
            generated_scenarios = json.load(scenarios_file)

        with ProcessPoolExecutor(max_workers=24) as executor:
            for robustness, trace_idx in executor.map(load_and_process_active_learning_data, trace_file_paths):
                generated_scenarios[trace_idx]["robustness"] = robustness
    else:
        generated_scenarios = []

    return generated_scenarios

def setup_simulation():
    HOME = os.environ["HOME"]
    simulation_path = HOME + "/apollo_routing_sender/"
    env_simulation = os.environ.copy()
    env_simulation["PATH"] = os.pathsep.join([simulation_path, env_simulation["PATH"]])
    subprocess.run(["conda", "run", "-n", "srunner", "python3", "co-sim_mj.py"], cwd=simulation_path, env=env_simulation, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

ACTIVE_LEARNING_LOOP = 4

if __name__ == "__main__":
    mutated_dir = "traceset_mutated/"
    for session in sorted(os.listdir(mutated_dir)):
        for loop_round in range(ACTIVE_LEARNING_LOOP):
            active_learning_trainset = get_active_learning_trainset_parrellel(session)
            print("Reading training data...")
            dataset = get_trainset_parrellel(mutated_dir + session + "/")
            dataset.extend(active_learning_trainset.copy())
            train_surrogate_ensemble(dataset, session)
            del dataset

            generate_one_scenario(mutated_dir + session + "/", session, active_learning_trainset)
            del active_learning_trainset

            setup_simulation()

            gc.collect()
