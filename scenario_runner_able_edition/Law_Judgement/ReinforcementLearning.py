#!/usr/bin/env python3

import os
import gc
import copy
from collections import deque
import random
import ujson as json

from torch import nn, optim
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from gflownet.generator.proxy.proxy_config import proxy_args
from gflownet.generator.proxy.utils import *

from gflownet.generator.generative_model.utils import *
from gflownet.generator.generative_model.dataset import GFNSet
from gflownet.generator.generative_model.gfn_config import args
from gflownet.generator.pre_process.transform_actions import decode

from GFN_trainsurrogate_ensemble import get_trainset_parrellel, SurrogateInferer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def Embedding(num_embeddings, embedding_dim, padding_idx=None):
    m = nn.Embedding(num_embeddings, embedding_dim, padding_idx=padding_idx)
    nn.init.normal_(m.weight, mean=0, std=embedding_dim ** -0.5)
    if padding_idx is not None:
        nn.init.constant_(m.weight[padding_idx], 0)
    return m

class DQN(nn.Module):
    def __init__(self, num_tokens, num_outputs, num_hid,
                 num_layers, max_len=60, dropout=0.1,
                 partition_init=150.0, use_checkpoint=False):
        super(DQN, self).__init__()
        self.input = nn.Linear(num_tokens * max_len, num_hid)

        hidden_layers = []
        for _ in range(num_layers):
            hidden_layers.append(nn.Dropout(dropout))
            hidden_layers.append(nn.ReLU())
            hidden_layers.append(nn.Linear(num_hid, num_hid))
        self.hidden = nn.Sequential(*hidden_layers)
        self.output = nn.Linear(num_hid, num_outputs)
        self.max_len = max_len
        self.num_tokens = num_tokens
        self.emb = Embedding(self.num_tokens, self.num_tokens)

        self.use_checkpoint = use_checkpoint

    def forward(self, x, return_all=False, lens=None):
        if not self.use_checkpoint:
            # print(x.shape)
            x = self.emb(x)
            # print(x.shape)
            x = x.reshape(x.size(0), -1)
            # print(x.shape)
            out = self.input(x)
            # print(out.shape)
            out = self.hidden(out)
            out = self.output(out)
            # print(out.shape)
            out = out.reshape(-1)
            return out
        else:
            x = self.emb(x)
            x = x.reshape(x.size(0), -1)
            out = checkpoint(self.input, x, use_reentrant=False)
            out = checkpoint(self.hidden, out, use_reentrant=False)
            out = checkpoint(self.output, out, use_reentrant=False)
            out = out.reshape(-1)
            return out

class ReplayBuffer:
    def __init__(self, minibatch_size=4, maxlen=1024):
        self.minibatch_size = minibatch_size
        self.experiences = deque([], maxlen=maxlen)

    def push(self, cur_state, next_state, reward, cur_len):
        experience = {}
        experience["cur_state"] = cur_state
        experience["next_state"] = next_state
        experience["reward"] = reward
        experience["cur_len"] = cur_len
        self.experiences.append(experience)

    def sample(self):
        return random.sample(self.experiences, self.minibatch_size)

    def __len__(self):
        return len(self.experiences)

def train_epoch(params, proxy_model, dqn_local, dqn_target, optimizer, criterion, replaybuffer,
                eps=0.05, gamma=0.5, update_step=4):
    batch_size = params.batch_size
    max_len = params.max_length + 1
    actions_list = params.actions_list
    actions_index = params.actions_index
    actions_category = params.actions_category

    cur_len = 1
    state = torch.LongTensor(batch_size, max_len)
    state.fill_(params.pad_index)
    state[:,0].fill_(params.bos_index)
    while cur_len < max_len:
        cur_action_index = actions_index[actions_category[cur_len-1]]

        # Epsilon-greedy action selection
        dqn_local.eval()
        all_rewards = torch.zeros((batch_size, cur_action_index[1] - cur_action_index[0])).to(device)
        next_state = state.detach().clone().to(device)
        with torch.no_grad():
            for action_index in range(cur_action_index[0], cur_action_index[1]):
                next_state[:,cur_len].fill_(action_index)
                all_rewards[:,(action_index - cur_action_index[0])] = dqn_local(next_state[:,1:])
        dqn_local.train()
        exploitation_action = all_rewards.argmax(axis=1).cpu() + cur_action_index[0]
        random_action = torch.randint(cur_action_index[0], cur_action_index[1], (batch_size,))
        eps_tensor = torch.rand(batch_size)
        action = torch.where(eps_tensor > eps, exploitation_action, random_action)

        # Use action sequence as state, so next_state can be represented by cur_state and action
        cur_state = state.detach().clone().to(device)
        state[:,cur_len] = action
        next_state = state.detach().clone().to(device)
        if cur_len < max_len - 1:
            reward = torch.zeros((batch_size,))
        else:
            reward = proxy_model.infer_surrogate_ensemble(state[:,1:])
        replaybuffer.push(cur_state, next_state, reward.detach().clone().to(device), cur_len)

        if len(replaybuffer) >= replaybuffer.minibatch_size:
            replaybatch = replaybuffer.sample()
            for experience in replaybatch:
                Q_expected = dqn_local(experience["cur_state"][:,1:])

                if experience["cur_len"]+1 >= max_len-1:
                    Q_target = experience["reward"]
                else:
                    next_state = experience["next_state"].clone()
                    next_action_index = actions_index[actions_category[experience["cur_len"]]]
                    all_Q_next = torch.zeros((batch_size, next_action_index[1] - next_action_index[0])).to(device)
                    with torch.no_grad():
                        for action_index in range(next_action_index[0], next_action_index[1]):
                            next_state[:,(experience["cur_len"]+1)].fill_(action_index)
                            all_Q_next[:,(action_index - next_action_index[0])] = dqn_target(next_state[:,1:])
                    Q_next = all_Q_next.max(1)[0]
                    Q_target = experience["reward"] + (gamma * Q_next)

                loss = criterion(Q_expected, Q_target)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if cur_len % update_step:
                dqn_target.load_state_dict(dqn_local.state_dict())

        cur_len += 1

def infer_samples(gflownet_set, params, dqn_local, eps=0.05):
    batch_size = params.batch_size
    max_len = params.max_length + 1
    actions_list = params.actions_list
    actions_index = params.actions_index
    actions_category = params.actions_category

    cur_len = 1
    state = torch.LongTensor(batch_size, max_len)
    state.fill_(params.pad_index)
    state[:,0].fill_(params.bos_index)
    dqn_local.eval()
    while cur_len < max_len:
        cur_action_index = actions_index[actions_category[cur_len-1]]

        all_rewards = torch.zeros((batch_size, cur_action_index[1] - cur_action_index[0])).to(device)
        next_state = state.detach().clone().to(device)
        with torch.no_grad():
            for action_index in range(cur_action_index[0], cur_action_index[1]):
                next_state[:,cur_len].fill_(action_index)
                all_rewards[:,(action_index - cur_action_index[0])] = dqn_local(next_state[:,1:])

        exploitation_action = all_rewards.argmax(axis=1).cpu() + cur_action_index[0]
        random_action = torch.randint(cur_action_index[0], cur_action_index[1], (batch_size,))
        eps_tensor = torch.rand(batch_size)
        action = torch.where(eps_tensor > eps, exploitation_action, random_action)
        state[:,cur_len] = action

        cur_len += 1

    samples = []
    for single in state:
        if judge_generated(single[1:],actions_category=actions_category,actions_index=actions_index):
            samples.append(list(single[1:].numpy()))
    result = transform2json(samples, gflownet_set.proxy_actions_list)
    print("New samples {}".format(len(result)))
    return result

DQN_BATCHES = 4

def generate_samples_with_reinforcementlearning(session, gflownet_set):
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

    save_ckpt_path = "gflownet/generator/ckpt/" + session + "/dqn.pth"
    if os.path.isfile(save_ckpt_path):
        print("Use trained DQN.")

        dqn_local = torch.load(save_ckpt_path)
        dqn_local = dqn_local.to(device)

        results = []
        for dqn_batch in range(DQN_BATCHES):
            results.extend(infer_samples(gflownet_set, params, dqn_local))
        return results

    proxy_model = SurrogateInferer(session)

    dqn_local = DQN(num_tokens=gflownet_set.num_tokens,
                        num_outputs=1,
                        num_hid=proxy_args.num_hid,
                        num_layers=proxy_args.num_layers,
                        dropout=0.1,
                        max_len=gflownet_set.max_len,
                        use_checkpoint=True).to(device)
    dqn_target = DQN(num_tokens=gflownet_set.num_tokens,
                        num_outputs=1,
                        num_hid=proxy_args.num_hid,
                        num_layers=proxy_args.num_layers,
                        dropout=0.1,
                        max_len=gflownet_set.max_len,
                        use_checkpoint=True).to(device)
    dqn_target.load_state_dict(dqn_local.state_dict())
    dqn_target.eval()
    optimizer = optim.Adam(dqn_local.parameters(), lr=proxy_args.lr)

    lr = proxy_args.lr
    criterion = nn.MSELoss()
    stage = 1

    replaybuffer = ReplayBuffer()

    print("Start training DQN.")

    for epoch in range(1, args.n_train_steps + 1):
        print("epoch:", epoch)
        train_epoch(params, proxy_model, dqn_local, dqn_target, optimizer, criterion, replaybuffer)
        if epoch in proxy_args.stage_epoch:
            stage += 1
            lr /= proxy_args.lr_decay
            adjust_learning_rate(optimizer, lr)

    save_ckpt_path = "gflownet/generator/ckpt/" + session + "/dqn.pth"
    torch.save(dqn_local, save_ckpt_path)

    results = []
    for dqn_batch in range(DQN_BATCHES):
        results.extend(infer_samples(gflownet_set, params, dqn_local))
    return results

def generate_one_scenario(subdir_path, session):
    actionseq_path = "generated_actionseq/" + session + "_rl.json"
    if os.path.isfile(actionseq_path):
        with open(actionseq_path) as actionseq_file:
            generated_actionseq = json.load(actionseq_file)
    else:
        dataset = get_trainset_parrellel(subdir_path)
        gflownet_set = GFNSet(dataset, train=True)
        del dataset
        gc.collect()
        generated_actionseq = generate_samples_with_reinforcementlearning(session, gflownet_set)
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
    with open("generated_scenarios/" + session + "_rl.json", 'w') as scenarios_file:
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
