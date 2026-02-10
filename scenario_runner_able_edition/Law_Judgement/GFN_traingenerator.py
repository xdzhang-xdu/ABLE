#!/usr/bin/env python
import os
import gc
import copy
import tqdm
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import torch.nn.functional as F

from gflownet.generator.generative_model.model import TransformerModel, make_mlp
from gflownet.generator.generative_model.utils import *
from gflownet.generator.generative_model.dataset import GFNSet
from gflownet.generator.generative_model.gfn_config import args
from gflownet.generator.pre_process.transform_actions import decode

from GFN_trainsurrogate_ensemble import get_trainset_parrellel, SurrogateInferer

def create_next_words_mapping_tensor(gflownet_set, params):
    next_words_mapping = torch.zeros(params.n_words, params.n_words)

    for actionseq in gflownet_set.actions:
        for seqidx in range(gflownet_set.max_len - 1):
            action = actionseq[seqidx]
            actionidx = gflownet_set.actions_to_index[action]
            next_action = actionseq[seqidx+1]
            next_actionidx = gflownet_set.actions_to_index[next_action]

            next_words_mapping[actionidx, next_actionidx] = 1.0

    return next_words_mapping

def get_trajectories_directed_distance(trajectory1, trajectory2, probs1, probs2):
    directed_distance = 0.0
    samesincestart = True
    for idx in range(len(trajectory1)):
        if samesincestart and trajectory1[idx] == trajectory2[idx]:
            continue

        samesincestart = False
        directed_distance = directed_distance - np.log(probs1[idx]) - np.log(probs2[idx])

    return directed_distance

def get_discrepancy_coefficient(trajectory1, trajectory2):
    num_shared_actions = len(set(trajectory1) & set(trajectory2))
    return 1 - num_shared_actions / len(trajectory1)

samples_g = None
probs_generated_g = None

def get_directed_distance_parrellel(sample_idx_tuple):
    sample1_idx, sample2_idx = sample_idx_tuple
    directed_distance = get_trajectories_directed_distance(samples_g[sample1_idx], samples_g[sample2_idx],
                                                           probs_generated_g[sample1_idx], probs_generated_g[sample2_idx])
    discrepancy_coefficient = get_discrepancy_coefficient(samples_g[sample1_idx], samples_g[sample2_idx])
    return sample_idx_tuple, directed_distance, discrepancy_coefficient

def generate_samples_with_gfn(session, gflownet_set, specs_covered_flag):
    if not os.path.isdir("gflownet/generator/ckpt/" + session):
        os.mkdir("gflownet/generator/ckpt/" + session)
    save_ckpt_path = "gflownet/generator/ckpt/" + session + "/gflownet.pth"
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
    next_words_mapping = create_next_words_mapping_tensor(gflownet_set, params)
    x = gflownet_set[0]
    # print(len(params.actions_category))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logZ = torch.zeros((1,)).to(device)
    n_hid = args.n_hid
    n_layers = args.n_layers
    mlp = make_mlp([params.emb_dim] + [n_hid] * n_layers + [params.n_words]).to(device)
    model = TransformerModel(params, mlp).to(device)
    P_B = 1 # DAG & sequence generation => tree 
    optim = torch.optim.Adam([ {'params':model.parameters(), 'lr':0.0001}, {'params':[logZ], 'lr':0.01} ])
    logZ.requires_grad_()
    losses_TB = []
    zs_TB = []
    rewards_TB = []
    l1log_TB = []
    proxy_model = SurrogateInferer(session)
    batch_size = params.batch_size
    max_len = params.max_length + 1
    actions_list = params.actions_list
    actions_index = params.actions_index
    actions_category = params.actions_category
    # proxy_actions_category = params.proxy_actions_category
    n_train_steps = args.n_train_steps
    # print(x[1].shape)
    # print(judge_generated(x[0],actions_category=params.proxy_actions_category,actions_index=params.proxy_actions_index))
    # sys.exit(0)
    for it in tqdm.trange(n_train_steps):
        nan_flag = False
        generated = torch.LongTensor(batch_size, max_len)  # upcoming output
        generated.fill_(params.pad_index)                  # fill upcoming ouput with <PAD>
        generated[:,0].fill_(params.bos_index)             # <BOS> (start token), initial state

        # Length of already generated sequences : 1 because of <BOS>
        #gen_len = (generated != params.pad_index).long().sum(dim=1)
        gen_len = torch.LongTensor(batch_size,).fill_(1) # (batch_size,)
        # 1 (True) if the generation of the sequence is not yet finished, 0 (False) otherwise
        unfinished_sents = gen_len.clone().fill_(1) # (batch_size,)
        # Length of already generated sequences : 1 because of <BOS>
        cur_len = 1

        # Z_test = model(generated[:,:cur_len].to(device), lengths=gen_len.to(device))
        # #Z_test = Z_test[:,0].squeeze(1).exp().to(device)
        # Z_test = Z_test.sum(dim=1).squeeze(1).exp().to(device)
        # print(Z_test)

        Z = logZ.exp()

        flag = True
        if flag :
            # detached form of TB
            ll_diff = torch.zeros((batch_size,)).to(device)
            ll_diff += logZ
        else :
            # non-detached form of TB ojective, where we multiply everything before doing the logarithm
            in_probs = torch.ones(batch_size, dtype=torch.float, requires_grad=True).to(device)

        while cur_len < max_len:
            state = generated[:,:cur_len] + 0 # (bs, cur_len)
            tensor = model(state.to(device), lengths=gen_len.to(device)) # (bs, cur_len, vocab_size)
            #scores = tensor[:,0] # (bs, vocab_size) : use last word for prediction
            scores = tensor.sum(dim=1) # (bs, vocab_size)
            
            # fixed length generation
            cur_action_index = actions_index[actions_category[cur_len-1]]
            
            scores = scores.log_softmax(1)
            
            sample_temperature = 100

            current_words = generated[:,cur_len-1]
            probs_override = next_words_mapping[current_words].to(device)
            
            # scores = softmax_norm(scores,batch_size,params.n_words)
            # break
            #probs = F.softmax(scores / sample_temperature, dim=1)
            probs = torch.exp(F.log_softmax(scores / sample_temperature, dim=1))
            if cur_len > 1:
                probs = torch.where(probs_override > 0., probs, 0.)
            """
            for index in range(0,cur_action_index[0]):
                probs[:,index] = 1e-8#0
            for index in range(cur_action_index[1],len(actions_list)):
                probs[:,index] = 1e-8#0
            """
            probs_arange = torch.tile(torch.arange(probs.shape[1], device=device), (probs.shape[0], 1))
            probs = torch.where(torch.logical_or(probs_arange < cur_action_index[0], probs_arange >= cur_action_index[1]), 0., probs)
            #probs = torch.where(torch.isnan(probs),torch.full_like(probs,1e-8),probs)
            try:
                next_words = torch.multinomial(probs, 1).squeeze(1)
            except:
                print("nan_flag is True!")
                nan_flag = True
                break
            
            # update generations / lengths / finished sentences / current length
            generated[:,cur_len] = next_words.cpu() * unfinished_sents + params.pad_index * (1 - unfinished_sents)
            gen_len.add_(unfinished_sents) # add 1 to the length of the unfinished sentences
            unfinished_sents.mul_(next_words.cpu().ne(params.eos_index).long()) # as soon as we generate <EOS>, set unfinished_sents to 0
            cur_len = cur_len + 1

            # loss
            if flag :
                #sample_in_probs = probs.gather(1, next_words.unsqueeze(-1)).squeeze(1)
                #sample_in_probs[unfinished_sents == 0] = 1.
                #ll_diff += sample_in_probs.log()
                
                ll_diff += scores.gather(1, next_words.unsqueeze(-1)).squeeze(1)
            else :
                sample_in_probs = probs.gather(1, next_words.unsqueeze(-1)).squeeze(1)
                sample_in_probs[unfinished_sents == 0] = 1.
                in_probs = in_probs * sample_in_probs

            # stop when there is a <EOS> in each sentence, or if we exceed the maximul length
            if unfinished_sents.max() == 0:
                break
        if nan_flag == True:
            #torch.save(model, save_ckpt_path)
            nan_flag = False
            continue

        generated = generated.apply_(lambda index : 0 if index == params.pad_index or index == params.eos_index else index)
        #R = reward_function(generated, reward_coef, lambda_, beta).to(device)
        # generated =  [float("".join([str(s_i) for s_i in s])) for s in generated.tolist()]
        # R = reward_function2(generated, reward_coef, lambda_, beta).to(device) 
        flag_list = []
        
        
        generated = generated[:,1:]
        for single in generated:
            flag_list.append(judge_generated(single,actions_category=actions_category,actions_index=actions_index))
        flag_index = 0
        
        
        R = proxy_model.infer_surrogate_ensemble(generated, specs_covered_flag)
        R = R.exp()
        R = torch.where(R>1e-8, R, 1e-8)
        for r in R:
            # print(flag_index)
            if flag_list[flag_index] == True:
                flag_index = flag_index + 1
                continue
            else:
                R[flag_index] = 1e-8
                flag_index = flag_index + 1
                continue
        optim.zero_grad()
        if flag :
            ll_diff -= R.log().to(device)
            loss = (ll_diff**2).sum()/batch_size
        else :
            Z = Z.to(device)
            in_probs = in_probs.to(device)
            R = R.to(device)
            loss = ((Z*in_probs / R).log()**2).sum()/batch_size
        R = R.detach()
        loss.backward()
        optim.step()

        losses_TB.append(loss.item())
        zs_TB.append(Z.item())
        rewards_TB.append(R.mean().cpu())
        torch.cuda.empty_cache()

        if (it+1)%100==0:
            torch.save(model, save_ckpt_path)
            print('\nloss =', np.array(losses_TB[-100:]).mean(), 'Z =', Z.item(), "R =", np.array(rewards_TB[-100:]).mean())
    torch.save(model, save_ckpt_path)

    # generating process
    samples = []
    probs_generated = torch.zeros((args.generated_number * batch_size, params.max_length)).to(device)
    model = torch.load(save_ckpt_path)
    model.eval()
    # 100 means you want to generate 100 batch_size new test data
    # since the batch_size here is 2
    # means 200 generated data
    for it in tqdm.trange(args.generated_number):
        nan_flag = False
        generated = torch.LongTensor(batch_size, max_len)  # upcoming output
        generated.fill_(params.pad_index)                  # fill upcoming ouput with <PAD>
        generated[:,0].fill_(params.bos_index)             # <BOS> (start token), initial state

        # Length of already generated sequences : 1 because of <BOS>
        #gen_len = (generated != params.pad_index).long().sum(dim=1)
        gen_len = torch.LongTensor(batch_size,).fill_(1) # (batch_size,)
        # 1 (True) if the generation of the sequence is not yet finished, 0 (False) otherwise
        unfinished_sents = gen_len.clone().fill_(1) # (batch_size,)
        # Length of already generated sequences : 1 because of <BOS>
        cur_len = 1

        while cur_len < max_len:
            state = generated[:,:cur_len] + 0 # (bs, cur_len)
            with torch.no_grad():
                tensor = model(state.to(device), lengths=gen_len.to(device)) # (bs, cur_len, vocab_size)
            #scores = tensor[:,0] # (bs, vocab_size) : use last word for prediction
            scores = tensor.sum(dim=1) # (bs, vocab_size)
            # fixed length generation
            cur_action_index = actions_index[actions_category[cur_len-1]]
            scores = scores.log_softmax(1)
            sample_temperature = 1
            current_words = generated[:,cur_len-1]
            probs_override = next_words_mapping[current_words].to(device)
            #probs = F.softmax(scores / sample_temperature, dim=1)
            probs = torch.exp(F.log_softmax(scores / sample_temperature, dim=1))
            if cur_len > 1:
                probs = torch.where(probs_override > 0., probs, 0.)
            """
            for index in range(0,cur_action_index[0]):
                probs[:,index] = 1e-8#0
            for index in range(cur_action_index[1],len(actions_list)):
                probs[:,index] = 1e-8#0
            """
            probs_arange = torch.tile(torch.arange(probs.shape[1], device=device), (probs.shape[0], 1))
            probs = torch.where(torch.logical_or(probs_arange < cur_action_index[0], probs_arange >= cur_action_index[1]), 0., probs)
            #next_words = torch.distributions.categorical.Categorical(probs=probs).sample()
            try:
                next_words = torch.multinomial(probs, 1).squeeze(1)
            except:
                nan_flag = True
                break
            # update generations / lengths / finished sentences / current length

            sample_in_probs = probs.gather(1, next_words.unsqueeze(-1)).squeeze(1)
            starting_batch = it * batch_size
            ending_batch = starting_batch + batch_size
            probs_generated[starting_batch:ending_batch,cur_len-1] = sample_in_probs / torch.sum(probs, dim=1)
            generated[:,cur_len] = next_words.cpu() * unfinished_sents + params.pad_index * (1 - unfinished_sents)
            gen_len.add_(unfinished_sents) # add 1 to the length of the unfinished sentences
            unfinished_sents.mul_(next_words.cpu().ne(params.eos_index).long()) # as soon as we generate <EOS>, set unfinished_sents to 0
            cur_len = cur_len + 1
        
            # stop when there is a <EOS> in each sentence, or if we exceed the maximul length
            if unfinished_sents.max() == 0:
                break

        #R = reward_function(generated, reward_coef, lambda_, beta).to(device)
        if nan_flag == True:
            nan_flag = False
            continue
        for single in generated:
            if judge_generated(single[1:],actions_category=actions_category,actions_index=actions_index):
                samples.append(single[1:].numpy().astype(int).tolist())

    result = transform2json(samples, gflownet_set.proxy_actions_list)
    print("New samples {}".format(len(result)))

    tso_data = {}
    tso_data["samples"] = samples
    probs_generated_ndarray = probs_generated.detach().cpu().numpy()
    tso_data["probs_generated"] = probs_generated_ndarray.astype(float).tolist()
    tso_data["reduced_idx_list"] = directed_dist_based_tso(samples, probs_generated_ndarray)
    return result, tso_data

def directed_dist_based_tso(samples, probs_generated, quantile=0.1):
    num_samples = len(samples)
    directed_distance_cache = np.full((num_samples, num_samples), float("inf"))
    discrepancy_coefficient_cache = np.ones((num_samples, num_samples))
    global samples_g
    global probs_generated_g
    samples_g = samples
    probs_generated_g = probs_generated

    sample_idx_tuples = []
    for sample1_idx in range(num_samples):
        for sample2_idx in range(sample1_idx+1, num_samples):
            sample_idx_tuples.append((sample1_idx, sample2_idx))
    with ProcessPoolExecutor(max_workers=24) as executor:
        for sample_idx_tuple, directed_distance, discrepancy_coefficient in executor.map(get_directed_distance_parrellel, sample_idx_tuples):
            sample1_idx, sample2_idx = sample_idx_tuple
            directed_distance_cache[sample1_idx][sample2_idx] = directed_distance
            discrepancy_coefficient_cache[sample1_idx][sample2_idx] = discrepancy_coefficient
    directed_dist_mod = directed_distance_cache * discrepancy_coefficient_cache
    tso_min_directed_distance = np.quantile(np.min(directed_dist_mod, axis=1), quantile)

    reduced_idx_set = set()
    for sample1_idx in range(num_samples):
        for sample2_idx in range(sample1_idx+1, num_samples):
            if sample2_idx in reduced_idx_set:
                continue
            if directed_dist_mod[sample1_idx][sample2_idx] < tso_min_directed_distance:
                reduced_idx_set.add(sample2_idx)
    print("Reserved: {}, reduced: {}, ratio: {}".format(len(samples) - len(reduced_idx_set), len(reduced_idx_set),\
                                                        len(reduced_idx_set) / len(samples)))
    
    return list(reduced_idx_set)

def active_learning_filter_covered_specs(active_learning_trainset):
    specs_covered_flag = [False] * len(active_learning_trainset[0]["robustness"])

    for history_scenario in active_learning_trainset:
        list_robustness = history_scenario["robustness"]
        for robustness_idx, robustness in enumerate(list_robustness):
            if robustness >= 0.:
                specs_covered_flag[robustness_idx] = True

    return specs_covered_flag[1:]

def generate_one_scenario(subdir_path, session, active_learning_trainset=[]):
    actionseq_path = "generated_actionseq/" + session + "_mk2.json"
    print(subdir_path)
    print(actionseq_path)

    cumulative_actionseq = []
    cumulative_tso_data = []
    if os.path.isfile(actionseq_path):
        with open(actionseq_path, 'r') as actionseq_file:
            cumulative_actionseq = json.load(actionseq_file)
    if os.path.isfile(actionseq_path.replace(".json", "_tsodata.json")):
        with open(actionseq_path.replace(".json", "_tsodata.json"), 'r') as tso_file:
            cumulative_tso_data = json.load(tso_file)

    print("Reading training data...")
    dataset = get_trainset_parrellel(subdir_path)
    dataset.extend(active_learning_trainset)
    gflownet_set = GFNSet(dataset, train=True)
    del dataset
    gc.collect()

    if len(active_learning_trainset) > 0:
        specs_covered_flag = active_learning_filter_covered_specs(active_learning_trainset)
    else:
        specs_covered_flag = None

    generated_actionseq, tso_data = generate_samples_with_gfn(session, gflownet_set, specs_covered_flag)
    cumulative_idx = len(cumulative_actionseq)
    for actionseq in generated_actionseq:
        scenario_idx = int(actionseq["ScenarioName"].replace("NO_", ""))
        actionseq["ScenarioName"] = "NO_" + str(scenario_idx + cumulative_idx)

    cumulative_actionseq.extend(generated_actionseq)
    cumulative_tso_data.append(tso_data)

    with open(actionseq_path, 'w') as actionseq_file:
        json.dump(cumulative_actionseq, actionseq_file, indent=4)
    with open(actionseq_path.replace(".json", "_tsodata.json"), 'w') as tso_file:
        json.dump(cumulative_tso_data, tso_file, indent=4)

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
    for actionseq in cumulative_actionseq:
        generated_scenario = copy.deepcopy(template_scenario)
        generated_scenario["ScenarioName"] = actionseq["ScenarioName"]
        generated_scenario["actions"] = actionseq["actions"]
        decode(generated_scenario)
        generated_scenarios.append(generated_scenario)
    with open("generated_scenarios/" + session + "_mk2.json", 'w') as scenarios_file:
        json.dump(generated_scenarios, scenarios_file, indent=4)

def generate_scenarios_in_batch(mutated_dir):
    for session in sorted(os.listdir(mutated_dir)):
        print("Using dataset:", mutated_dir + session + "/")
        generate_one_scenario(mutated_dir + session + "/", session)

if __name__ == '__main__':
    mutated_dir = "traceset_mutated/"
    args_terminal = sys.argv
    if len(args_terminal) == 2 and os.path.isdir(mutated_dir + args_terminal[1]):
        generate_one_scenario(mutated_dir, args_terminal[1])
    else:
        generate_scenarios_in_batch(mutated_dir)
