#!/usr/bin/env python3

import math
import ujson as json
from concurrent.futures import ProcessPoolExecutor

from torch import nn, optim
from torch.utils.data import DataLoader
from law_judgement_extended import Monitor
from gflownet.generator.pre_process.transform_actions import encode
from gflownet.generator.proxy.mlp_model import MLP
from gflownet.generator.proxy.dataset import ProxySet
from gflownet.generator.proxy.utils import *
from gflownet.generator.generative_model.proxy_model import proxy
from gflownet.generator.generative_model.utils import *
from gflownet.path_config import path_args

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

    return dataset_scenario

def get_trainset_parrellel(path_mutated):
    files = []
    for traceset_mutated in os.listdir(path_mutated):
        files.append(path_mutated + traceset_mutated)

    dataset = []
    with ProcessPoolExecutor(max_workers=8) as executor:
        for dataset_scenario in executor.map(load_and_process_json_data, files):
            dataset.extend(dataset_scenario)

    return dataset

def load_surrogate_hyperparam(session, formulae_idx):
    surrogate_hyperparam_dir = "gflownet/generator/proxy/hyperparam/"
    surrogate_hyperparam_path = os.path.join(surrogate_hyperparam_dir, session + ".json")
    with open(surrogate_hyperparam_path, 'r') as hyperparam_config_file:
        hyperparam_metadict = json.load(hyperparam_config_file)
    hyperparam_dict = hyperparam_metadict["sub_law_violation_" + str(formulae_idx)]

    hyperparam = AttrDict({
        "lr": hyperparam_dict["learning_rate"],
        "lr_decay": hyperparam_dict["learning_rate_decay"],
        "stage_epoch": [16,32,64,128],
        "batch_size": hyperparam_dict["batch_size"],
        "num_hid": hyperparam_dict["num_hid"],
        "num_layers": hyperparam_dict["num_layers"],
        "dropout": hyperparam_dict["dropout"],
        "num_tokens": hyperparam_dict["num_tokens"],
        "max_len": hyperparam_dict["max_len"],
    })
    return hyperparam

def train_surrogate(dataset, session, formulae_idx):
    ensemble_dir = path_args.proxy_path.format(session + "_ensemble")
    if not os.path.isdir(ensemble_dir):
        os.mkdir(ensemble_dir)
    ensemble_path = os.path.join(ensemble_dir, session + "_" + str(formulae_idx) + ".pth")

    hyperparam = load_surrogate_hyperparam(session, formulae_idx)

    train_dataset = ProxySet(dataset, train=True, robustness_idx=formulae_idx)
    train_dataloader = DataLoader(train_dataset, batch_size=hyperparam.batch_size, shuffle=True)
    val_dataset = ProxySet(dataset, train=False, robustness_idx=formulae_idx)
    val_dataloader = DataLoader(val_dataset, batch_size=hyperparam.batch_size)

    model = MLP(num_tokens=train_dataset.num_tokens,
                num_outputs=1,
                num_hid=hyperparam.num_hid,
                num_layers=hyperparam.num_layers,
                dropout=hyperparam.dropout,
                max_len=train_dataset.max_len,
                use_checkpoint=True)
    model = model.to(device)

    lr = hyperparam.lr
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    for epoch in range(1, proxy_args.max_epoch + 1):
        model.train()
        train_losses = []
        for inputs, target in train_dataloader:
            outputs = model(inputs.to(device))
            loss = criterion(outputs.to(torch.float32), target.to(device).to(torch.float32))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        model.eval()
        val_losses = []
        with torch.no_grad():
            for inputs, target in val_dataloader:
                outputs = model(inputs.to(device))
                loss = criterion(outputs, target.to(device))

                val_losses.append(loss.item())

        avg_val_loss = np.mean(val_losses)
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_state = model.state_dict()
        
        if epoch in hyperparam.stage_epoch:
            model.load_state_dict(best_state)
            lr *= hyperparam.lr_decay
            adjust_learning_rate(optimizer, lr)
            print("Best loss:", best_val_loss)
            print("epoch: {}, loss: {}, lr: {}".format(epoch, avg_val_loss, lr))
    print("Formulae:", formulae_idx, "best loss:", best_val_loss, "end epoch:", epoch)

    torch.save(best_state, ensemble_path)

    del optimizer
    del model
    torch.cuda.empty_cache()

def train_surrogate_ensemble(dataset, session):
    num_formulaes = len(dataset[0]["robustness"]) - 1
    for formulae_idx in range(1, num_formulaes+1):
        train_surrogate(dataset, session, formulae_idx)

def get_proxy_model(proxy_path, hyperparam):
    proxy_model = proxy(num_tokens=hyperparam.num_tokens,
                        num_outputs=1,
                        num_hid=hyperparam.num_hid,
                        num_layers=hyperparam.num_layers,
                        dropout=hyperparam.dropout,
                        max_len=hyperparam.max_len)
    proxy_model.load_state_dict(torch.load(proxy_path,map_location='cpu'))
    return proxy_model

class SurrogateInferer():
    def __init__(self, session):
        self.session = session
        files = os.listdir(path_args.proxy_path.format(session + "_ensemble"))
        num_formulaes = len(files)
        self.num_formulaes = num_formulaes
        self.proxy_model_dict = {}

        for formulae_idx in range(1, num_formulaes+1):
            proxy_path = os.path.join(path_args.proxy_path.format(session + "_ensemble"), session + "_" + str(formulae_idx) + ".pth")
            if not os.path.isfile(proxy_path):
                print("Surrogate model state file: {} not found.".format(proxy_path))
                exit()
            hyperparam = load_surrogate_hyperparam(session, formulae_idx)
            proxy_model = get_proxy_model(proxy_path, hyperparam)
            proxy_model.eval()
            self.proxy_model_dict[formulae_idx] = proxy_model

    def infer_surrogate(self, formulae_idx, actionseqs):
        proxy_model = self.proxy_model_dict[formulae_idx]
        if torch.is_tensor(actionseqs):
            reward = proxy_model(actionseqs)
            robustness = reward.detach().cpu()
            return robustness
        elif isinstance(actionseqs, list):
            num_actionseq = len(actionseqs)
            robustness_list = []
            hyperparam = load_surrogate_hyperparam(self.session, formulae_idx)
            for split_idx in range(math.ceil(num_actionseq / hyperparam.batch_size)):
                starting_idx = split_idx * hyperparam.batch_size
                ending_idx = starting_idx + hyperparam.batch_size
                actionseq_sublist = actionseqs[starting_idx : min(num_actionseq, ending_idx)]

                actionseq_tensor = torch.LongTensor(hyperparam.batch_size, hyperparam.max_len)
                for batch_idx, actionseq in enumerate(actionseq_sublist):
                    actionseq_tensor[batch_idx] = torch.tensor(actionseq, dtype=torch.long)
                if len(actionseq_sublist) < hyperparam.batch_size:
                    for batch_idx in range(len(actionseq_sublist), hyperparam.batch_size):
                        actionseq_tensor[batch_idx] = torch.tensor(actionseq_sublist[-1], dtype=torch.long)

                reward = proxy_model(actionseq_tensor)
                robustness_list.extend(reward.detach().cpu().numpy().tolist())
            robustness_list = robustness_list[:num_actionseq]
            return robustness_list

    def infer_surrogate_ensemble(self, actionseqs, specs_covered_flag=None):
        if torch.is_tensor(actionseqs):
            summary_robustness_tensor = torch.full((actionseqs.shape[0], self.num_formulaes), float("-inf"))
            for formulae_idx in range(1, self.num_formulaes+1):
                robustness_tensor = self.infer_surrogate(formulae_idx, actionseqs)
                summary_robustness_tensor[:,formulae_idx-1] = robustness_tensor

                if not specs_covered_flag is None and specs_covered_flag[formulae_idx-1]:
                    summary_robustness_tensor[:,formulae_idx-1].fill_(float("-inf"))

            ensemble_robustness_tensor = torch.max(summary_robustness_tensor, dim=1)[0]
            return ensemble_robustness_tensor
        elif isinstance(actionseqs, list):
            robustness_metalist = []
            for formulae_idx in range(1, self.num_formulaes+1):
                robustness_list = self.infer_surrogate(formulae_idx, actionseqs)
                robustness_metalist.append(robustness_list)

                if not specs_covered_flag is None and specs_covered_flag[formulae_idx-1]:
                    for robustness_idx in range(len(robustness_list)):
                        robustness_list[robustness_idx] = float("-inf")

            num_actionseq = len(actionseqs)
            ensemble_robustness_list = [float("-inf")] * num_actionseq
            for formulae_idx in range(0, self.num_formulaes):
                for actionseq_idx in range(num_actionseq):
                    if robustness_metalist[formulae_idx][actionseq_idx] > ensemble_robustness_list[actionseq_idx]:
                        ensemble_robustness_list[actionseq_idx] = robustness_metalist[formulae_idx][actionseq_idx]
            return ensemble_robustness_list

    def infer_surrogate_fragment(self, actionseqs, specs_covered_flag=None):
        if torch.is_tensor(actionseqs):
            summary_robustness_tensor = torch.full((actionseqs.shape[0], self.num_formulaes), float("-inf"))
            for formulae_idx in range(1, self.num_formulaes+1):
                robustness_tensor = self.infer_surrogate(formulae_idx, actionseqs)
                summary_robustness_tensor[:,formulae_idx-1] = robustness_tensor

                if not specs_covered_flag is None and specs_covered_flag[formulae_idx-1]:
                    summary_robustness_tensor[:,formulae_idx-1].fill_(float("-inf"))

            return summary_robustness_tensor
        elif isinstance(actionseqs, list):
            robustness_metalist = []
            for formulae_idx in range(1, self.num_formulaes+1):
                robustness_list = self.infer_surrogate(formulae_idx, actionseqs)
                robustness_metalist.append(robustness_list)

                if not specs_covered_flag is None and specs_covered_flag[formulae_idx-1]:
                    for robustness_idx in range(len(robustness_list)):
                        robustness_list[robustness_idx] = float("-inf")

            return robustness_metalist

if __name__ == '__main__':
    mutated_dir = "traceset_mutated/"
    for session in sorted(os.listdir(mutated_dir)):
        dataset = get_trainset_parrellel(mutated_dir + session + "/")
        train_surrogate_ensemble(dataset, session)