#!/usr/bin/env python3

import ujson as json
from concurrent.futures import ProcessPoolExecutor
from law_judgement_extended import Monitor

import optuna

from torch import nn, optim
from torch.utils.data import DataLoader
from gflownet.generator.pre_process.transform_actions import encode
from gflownet.generator.proxy.mlp_model import MLP
from gflownet.generator.proxy.dataset import ProxySet
from gflownet.generator.proxy.utils import *

NUM_EPOCHS = 4
NUM_TRIALS = 50

global_dataset = []
global_formulae_idx = 0

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
    for traceset_mutated in os.listdir(path_mutated):
        files.append(path_mutated + traceset_mutated)

    dataset = []
    with ProcessPoolExecutor(max_workers=24) as executor:
        for dataset_scenario in executor.map(load_and_process_json_data, files):
            dataset.extend(dataset_scenario)

    return dataset

def objective(trial):
    lr = trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True)
    lr_decay = trial.suggest_float("learning_rate_decay", 1e-2, 1.0, log=True)
    stage_epoch = [16,32,64,128]
    trial.set_user_attr('batch_size', 256)
    num_hid = trial.suggest_int("num_hid", 128, 1024)
    num_layers = trial.suggest_int("num_layers", 1, 20)
    dropout = trial.suggest_float("dropout", 0.1, 0.5)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_dataset = ProxySet(global_dataset, train=True, robustness_idx=global_formulae_idx)
    train_dataloader = DataLoader(train_dataset, batch_size=trial.user_attrs['batch_size'], shuffle=True)
    val_dataset = ProxySet(global_dataset, train=False, robustness_idx=global_formulae_idx)
    val_dataloader = DataLoader(val_dataset, batch_size=trial.user_attrs['batch_size'])

    trial.set_user_attr('num_tokens', train_dataset.num_tokens)
    trial.set_user_attr('max_len', train_dataset.max_len)

    model = MLP(num_tokens=train_dataset.num_tokens,
                num_outputs=1,
                num_hid=num_hid,
                num_layers=num_layers,
                dropout=dropout,
                max_len=train_dataset.max_len,
                use_checkpoint=True)
    model = model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    for epoch in range(NUM_EPOCHS):
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

        trial.report(avg_val_loss, epoch)
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss

        if trial.should_prune():
            del optimizer
            del model
            torch.cuda.empty_cache()
            raise optuna.exceptions.TrialPruned()
        
        if epoch in stage_epoch:
            lr *= lr_decay
            adjust_learning_rate(optimizer, lr)

    del optimizer
    del model
    torch.cuda.empty_cache()

    return best_val_loss

def get_current_formulae_idx_in_saved_file(session):
    surrogate_hyperparam_dir = "gflownet/generator/proxy/hyperparam/"
    if not os.path.isdir(surrogate_hyperparam_dir):
        os.mkdir(surrogate_hyperparam_dir)
    surrogate_hyperparam_path = os.path.join(surrogate_hyperparam_dir, session + ".json")

    if os.path.isfile(surrogate_hyperparam_path):
        with open(surrogate_hyperparam_path, 'r') as hyperparam_config_file:
            hyperparam_metadict = json.load(hyperparam_config_file)
    else:
        hyperparam_metadict = {}

    violation_formulae_path = "violation_formulae.json"
    if os.path.isfile(violation_formulae_path):
        with open(violation_formulae_path, 'r') as violation_formulae_file:
            violation_formulae_dict = json.load(violation_formulae_file)
    del violation_formulae_dict["all_rules"]

    for formulae_idx in range(1, len(violation_formulae_dict)+1):
        if not "sub_law_violation_" + str(formulae_idx) in hyperparam_metadict:
            return formulae_idx
    return 0

def save_surrogate_hyperparam(hyperparam, fixedhyperparam, session, formulae_idx):
    surrogate_hyperparam_dir = "gflownet/generator/proxy/hyperparam/"
    if not os.path.isdir(surrogate_hyperparam_dir):
        os.mkdir(surrogate_hyperparam_dir)
    surrogate_hyperparam_path = os.path.join(surrogate_hyperparam_dir, session + ".json")

    if os.path.isfile(surrogate_hyperparam_path):
        with open(surrogate_hyperparam_path, 'r') as hyperparam_config_file:
            hyperparam_metadict = json.load(hyperparam_config_file)
    else:
        hyperparam_metadict = {}

    hyperparam["batch_size"] = fixedhyperparam["batch_size"]
    hyperparam["num_tokens"] = fixedhyperparam["num_tokens"]
    hyperparam["max_len"] = fixedhyperparam["max_len"]
    hyperparam_metadict["sub_law_violation_" + str(formulae_idx)] = hyperparam

    with open(surrogate_hyperparam_path, 'w') as hyperparam_config_file:
        json.dump(hyperparam_metadict, hyperparam_config_file, indent=4)
    print("sub_law_violation_" + str(formulae_idx) + " has been saved in:", surrogate_hyperparam_path)

def setup_study(session, formulae_idx):
    study = optuna.create_study(
        study_name="sub_law_violation_" + str(formulae_idx) + " of " + session,
        direction="minimize",
        pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=5)
    )

    study.optimize(objective, n_trials=NUM_TRIALS, gc_after_trial=True, show_progress_bar=True)

    best_trial = study.best_trial
    save_surrogate_hyperparam(best_trial.params, best_trial.user_attrs, session, formulae_idx)

def main():
    global global_dataset

    mutated_dir = "traceset_mutated/"
    for session in sorted(os.listdir(mutated_dir)):
        formulae_idx = get_current_formulae_idx_in_saved_file(session)
        if formulae_idx == 0:
            break
        print("Hypertuning on: session {}, violation {}".format(session, formulae_idx))

        global_dataset = get_trainset_parrellel(mutated_dir + session + "/")

        global global_formulae_idx
        global_formulae_idx = formulae_idx
        setup_study(session, formulae_idx)

        break

if __name__ == '__main__':
    main()