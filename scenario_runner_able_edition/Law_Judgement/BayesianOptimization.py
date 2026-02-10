#!/usr/bin/env python3

import os
import gc
import copy
import re
import numpy as np
import ujson as json
from concurrent.futures import ProcessPoolExecutor

from gflownet.generator.generative_model.utils import *
from gflownet.generator.generative_model.dataset import GFNSet
from gflownet.generator.generative_model.gfn_config import args
from gflownet.generator.pre_process.transform_actions import decode

from GFN_trainsurrogate_ensemble import get_trainset_parrellel, SurrogateInferer

from bayes_opt import BayesianOptimization

def get_robustness(params, proxy_model, next_point_list):
    actionseq_tensor = torch.LongTensor(params.batch_size, params.max_length)
    for batch, next_point in enumerate(next_point_list):
        actionseq_tensor[batch] = torch.tensor(list(next_point.values()), dtype=torch.long)

    reward = proxy_model.infer_surrogate_ensemble(actionseq_tensor)
    return reward.detach().numpy().tolist()

def suggest_parrellel(idx, bo):
    return idx, bo.suggest()

BO_BATCHES = 4
BO_EPOCHES = 64

def generate_samples_with_bayesianopt(session, gflownet_set):
    print("Start Bayesian Optimization.")

    params = AttrDict({
        "n_words": len(gflownet_set.proxy_actions_list),
        "pad_index" : gflownet_set.pad_index,
        "eos_index" : gflownet_set.bos_index,
        "bos_index" : gflownet_set.bos_index,
        'max_length': gflownet_set.proxy_max_len,
        'actions_index': gflownet_set.proxy_actions_indexes,
        'actions_list': gflownet_set.proxy_actions_list,
        "actions_category": gflownet_set.proxy_actions_category,
        "emb_dim" : args.emb_dim,
        "batch_size": args.batch_size,
    })

    proxy_model = SurrogateInferer(session)

    pbounds = {}
    for idx, action in enumerate(gflownet_set.actions[0]):
        if "lane_position" in action:
            current_action = re.sub(r'lane_\d+\+\d+(\.\d+)?$', '', action)
        else:
            current_action = re.sub(r'\d+(\.\d+)?$', '', action)
        sindex = gflownet_set.proxy_actions_indexes[current_action][0]
        eindex = gflownet_set.proxy_actions_indexes[current_action][1]
        pbounds[str(idx)] = (sindex, eindex-1, int)

    bo_batch_list = []
    for bo_batch in range(BO_EPOCHES):
        bo_list = []
        for _ in range(params.batch_size):
            bo_list.append(BayesianOptimization(f=None, pbounds=pbounds, verbose=0, allow_duplicate_points=True))

        for epoch in range(1, 64 + 1):
            print("Batch:", bo_batch, "Epoch:", epoch)

            next_point_list = [{}] * params.batch_size
            with ProcessPoolExecutor(max_workers=24) as executor:
                for suggest_tuple in executor.map(suggest_parrellel, list(range(params.batch_size)), bo_list):
                    next_point_list[suggest_tuple[0]] = suggest_tuple[1]

            #target = get_robustness(params, proxy_model, **next_point)
            target_list = get_robustness(params, proxy_model, next_point_list)

            #bo.register(params=next_point, target=target)
            for bo_idx, bo in enumerate(bo_list):
                bo.register(params=next_point_list[bo_idx], target=target_list[bo_idx])

        bo_batch_list.extend(bo_list)

    samples = []
    for bo in bo_batch_list:
        actionseq = [bo.max["params"][actionidx] for actionidx in bo.max["params"]]
        if judge_generated(torch.tensor(actionseq, dtype=torch.long),
                           actions_category=params.actions_category,
                           actions_index=params.actions_index):
            samples.append(actionseq)
    result = transform2json(samples, gflownet_set.proxy_actions_list)
    print("New samples {}".format(len(result)))
    return result

def generate_one_scenario(subdir_path, session):
    actionseq_path = "generated_actionseq/" + session + "_bysopt.json"
    if os.path.isfile(actionseq_path):
        with open(actionseq_path) as actionseq_file:
            generated_actionseq = json.load(actionseq_file)
    else:
        dataset = get_trainset_parrellel(subdir_path)
        gflownet_set = GFNSet(dataset, train=True)
        del dataset
        gc.collect()
        generated_actionseq = generate_samples_with_bayesianopt(session, gflownet_set)
        with open(actionseq_path, 'w') as actionseq_file:
            json.dump(generated_actionseq, actionseq_file, indent=4)

    if os.path.isfile("trace/trace_" + session + ".json"):
        with open("trace/trace_" + session + ".json") as scenario_file:
            template_scenario = json.load(scenario_file)
        del template_scenario["trace"]
    elif os.path.isfile("trace/" + session + "/trace_" + session + ".json"):
        with open("trace/" + session + "/trace_" + session + ".json") as scenario_file:
            template_scenario = json.load(scenario_file)
        del template_scenario["trace"]
    else:
        print("No template trace file found.")
        return

    generated_scenarios = []
    for actionseq in generated_actionseq:
        generated_scenario = copy.deepcopy(template_scenario)
        generated_scenario["ScenarioName"] = actionseq["ScenarioName"]
        generated_scenario["actions"] = actionseq["actions"]
        decode(generated_scenario)
        generated_scenarios.append(generated_scenario)
    with open("generated_scenarios/" + session + "_bysopt.json", 'w') as scenarios_file:
        json.dump(generated_scenarios, scenarios_file, indent=4)

def generate_scenarios_in_batch(mutated_dir):
    for session in os.listdir(mutated_dir):
        print("Using dataset:", mutated_dir + session + "/")
        generate_one_scenario(mutated_dir + session + "/", session)

if __name__ == '__main__':
    mutated_dir = "traceset_mutated/"
    args_terminal = sys.argv
    if len(args_terminal) == 2 and os.path.isdir(mutated_dir + args_terminal[1]):
        generate_one_scenario(mutated_dir, args_terminal[1])
    else:
        generate_scenarios_in_batch(mutated_dir)
