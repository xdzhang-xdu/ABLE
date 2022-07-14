import torch
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset,DataLoader
import re 
import json


class trafficSet(Dataset):
    def __init__(self,path,train):
        with open(path,'r') as f:
              testset = json.load(f)
        actions_set = set()
        self.actions = []
        self.rewards = []
        self.data = []
        self.target = []
        for tset in testset:
            self.actions.append(tset['actions'])
            self.rewards.append(tset['robustness'][0])
            for action in tset['actions']:
                    actions_set.add(action)
        if train is True:
            self.data = self.actions[:int(len(self.actions)*0.8)]
            self.target = self.rewards[:int(len(self.actions)*0.8)]
        else:
            self.data = self.actions[int(len(self.actions)*0.8):]
            self.target = self.rewards[int(len(self.actions)*0.8):]
            
        self.max_len = len(self.actions[0]) + 1
        self.actions_list = sorted(list(actions_set))
        self.actions_to_index = {self.actions_list[i] : i  for i in range(len(self.actions_list))}
        self.actions_category = []
        self.actions_dict = {}
        self.actions_index = []
        i = 0
        action_string = re.sub(r'[0-9]+', '', self.actions_list[0])
        for action in self.actions_list:
            current_action =  action[:4] + re.sub(r'[0-9]+', '', action[4:])
            if current_action not in self.actions_category:
                self.actions_category.append(current_action)
                self.actions_index.append(i)
                self.actions_dict[current_action] = [action]
            else:
                self.actions_dict[current_action].append(action)
            i = i + 1
        self.actions_indexes= {}
        for i in range(len(self.actions_index)):
            if i != len(self.actions_index) -1 :
                self.actions_indexes[self.actions_category[i]] = [self.actions_index[i],self.actions_index[i+1]]
            else:
                self.actions_indexes[self.actions_category[i]] = [self.actions_index[i],len(self.actions_list)]
            i = i + 1
        self.actions_list = self.actions_list + [',','.'] # bos,eos(.) and pad(,) tokens
        self.actions_indexes[','] = [len(self.actions_list)-2,len(self.actions_list)-1] # pad_index(,)
        self.actions_indexes['.'] = [len(self.actions_list)-1,len(self.actions_list)] # bos_index and eos_index(.)
        self.pad_index = len(self.actions_list) - 2
        self.bos_index = len(self.actions_list) - 1
        # self.embeddings = Embedding(len(self.actions_list),emb_dim,self.actions_indexes[','][0])
    def __getitem__(self, index):
        actions = self.actions[index]
        actions_idx = []
        for action in actions:
            actions_idx.append(self.actions_to_index[action])
        # action = [self.actions_indexes['.'][0]] + action  # add <BOS> for every action
        action = torch.LongTensor(actions_idx)
        reward = self.rewards[index]
        reward = np.exp(reward)
        # print(index)
        return action,reward
    def __len__(self):
        return len(self.data)