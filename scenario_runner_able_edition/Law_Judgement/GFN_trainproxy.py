#!/usr/bin/env python

import os
import random
#import json
import ujson as json
from concurrent.futures import ProcessPoolExecutor

from law_judgement_extended import Monitor

from gflownet.generator.proxy.proxy_config import proxy_args
from gflownet.generator.pre_process.transform_actions import encode
from gflownet.generator.proxy.train_proxy import train_proxy

def load_and_process_json_data(file_name):
    with open(file_name, 'r') as trace_file:
        dataset_scenario = json.load(trace_file)

    max_len = 0
    for scenario in dataset_scenario:
        encode(scenario)

        monitor = Monitor(scenario)
        list_violations = monitor.continuous_monitor_for_violations()
        list_reward = list(list_violations.values())
        list_reward[0] = max(list_reward[1:])
        scenario["robustness"] = list_reward

        max_len = max(max_len, len(scenario["actions"]))
    
    print("actions length:", max_len, file_name)
    
    return dataset_scenario

def get_trainset_parrellel(path_mutated):
    files = []
    trainset = []

    for traceset_mutated in os.listdir(path_mutated):
        files.append(path_mutated + traceset_mutated)

    with ProcessPoolExecutor(max_workers=16) as executor:
        for dataset_scenario in executor.map(load_and_process_json_data, files):
            trainset.extend(dataset_scenario)

    return trainset

def get_motion_amount(actionseq):
    motion_amount = []
    idx = -1
    for action in actionseq:
        if "motion" in action:
            idx = int(action.split("+")[2])
        if idx > 0 and "destination+lane_position" in action:
            motion_amount.append(idx)
    return motion_amount

def get_trainset(path_mutated):
    trainset = []

    for traceset_mutated in os.listdir(path_mutated):
        with open(path_mutated + traceset_mutated, 'r') as trace_file:
            dataset_scenario = json.load(trace_file)
        
        print(traceset_mutated)
        for scenario in dataset_scenario:
            encode(scenario)
            #print(get_motion_amount(scenario["actions"]), len(scenario["actions"]))

            """
            monitor = Monitor(scenario)
            list_violations = monitor.continuous_monitor_for_violations()
            list_reward = list(list_violations.values())
            list_reward[0] = max(list_reward[1:])
            scenario["robustness"] = list_reward
            """
        
        #for action in dataset_scenario[0]["actions"]:
        #    print(action)
        
        trainset.extend(dataset_scenario)
        exit()

    return trainset

if __name__ == '__main__':
    mutated_folder = "traceset_mutated/"
    for scenario_name in os.listdir(mutated_folder):
        if os.path.isdir(mutated_folder + scenario_name):
            path_mutated = mutated_folder + scenario_name + "/"
            #get_trainset(path_mutated)
            train_proxy(proxy_args, get_trainset_parrellel(path_mutated), scenario_name)
